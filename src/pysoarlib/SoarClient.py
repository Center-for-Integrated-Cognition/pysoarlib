import logging
from threading import Thread
import traceback
from time import sleep
from typing import Optional

from pysoarlib.util.sml import sml
from pysoarlib.Config import Config
from pysoarlib.TimeConnector import TimeConnector

# This is used for info relevant to developing the Python code;
# agent-related info is available via other configured loggers
logger = logging.getLogger(__name__)

DEFAULT_AGENT_NAME = "soaragent"


class SoarClient:
    """A wrapper class for creating and using a soar SML Agent"""

    def __init__(self, config: Config, print_handler=None):
        """Will create a soar kernel and agent

        print_handler determines how output is printed, defaults to python print

        Note: Still need to call connect() to register event handlers
        """

        if print_handler is not None:
            logger.info("Using provided print handler")
            self.print_handler = print_handler
        else:
            logger.info("No print handler provided, using python print")
            self.print_handler = print
        self.print_event_handlers = []

        self.connectors = {}

        self.config = config

        self.connected = False
        self.is_running = False
        self.queue_stop = False

        self.run_event_callback_id = -1
        self.print_event_callback_id = -1
        self.init_agent_callback_id = -1

        if self.config.remote_connection:
            logger.info("Creating remote Soar kernel connection...")
            self.kernel = sml.Kernel.CreateRemoteConnection()
        else:
            logger.info("Creating Soar kernel in new thread...")
            self.kernel = sml.Kernel.CreateKernelInNewThread()
            self.kernel.SetAutoCommit(False)

        if self.config.use_time_connector:
            self.add_connector("time", TimeConnector(self, **self.config.__dict__))
        self._create_soar_agent()

    def add_connector(self, name, connector):
        """Adds an AgentConnector to the agent"""
        self.connectors[name] = connector
        logger.info(f"Added connector {name}")

    def has_connector(self, name):
        """Returns True if the agent has an AgentConnector with the given name"""
        return name in self.connectors

    def get_connector(self, name):
        """Returns the AgentConnector with the given name, or None"""
        return self.connectors.get(name, None)

    def add_print_event_handler(self, handler):
        """calls the given handler during each soar print event,
        where handler is a method taking a single string argument"""
        self.print_event_handlers.append(handler)
        logger.info("Added print event handler")

    def start(self, steps: Optional[int] = None):
        """Will start the agent (uses another thread, so non-blocking)"""
        if self.is_running:
            return

        self.is_running = True
        thread = Thread(
            target=SoarClient._run_thread, name="Soar run thread", args=(self, steps)
        )
        logger.info("Starting Soar thread...")
        thread.start()

    def stop(self):
        """Tell the running thread to stop

        Note: Non-blocking, agent may run for a bit after this call finishes"""
        self.queue_stop = True

    def execute_command(self, cmd, print_res=False):
        """Execute a soar command and return result,
        write output to print_handler if print_res is True"""
        logger.debug(f"Executing Soar command: {cmd}")
        result = self.agent.ExecuteCommandLine(cmd, True).strip()  # type: ignore
        if print_res:
            self.print_handler(cmd)
            self.print_handler(result)
        logger.debug(f"Soar command result: {result}")
        return result

    def connect(self):
        """Register event handlers for agent and connectors"""
        if self.connected:
            return

        logger.info("Registering Soar event handlers...")
        self.run_event_callback_id = self.agent.RegisterForRunEvent(  # type: ignore
            sml.smlEVENT_BEFORE_INPUT_PHASE, SoarClient._run_event_handler, self
        )

        self.print_event_callback_id = self.agent.RegisterForPrintEvent(  # type: ignore
            sml.smlEVENT_PRINT, SoarClient._print_event_handler, self
        )

        self.init_agent_callback_id = self.kernel.RegisterForAgentEvent(  # type: ignore
            sml.smlEVENT_BEFORE_AGENT_REINITIALIZED,
            SoarClient._init_agent_handler,
            self,
        )

        for name, connector in self.connectors.items():
            logger.info(f"Calling connect() on connector {name}...")
            connector.connect()

        self.connected = True

        if self.config.start_running:
            self.start()

    def disconnect(self):
        """Unregister event handlers for agent and connectors"""
        if not self.connected:
            return

        logger.info("Unregistering Soar event handlers...")
        if self.run_event_callback_id != -1:
            self.agent.UnregisterForRunEvent(self.run_event_callback_id)  # type: ignore
            self.run_event_callback_id = -1

        if self.print_event_callback_id != -1:
            self.agent.UnregisterForPrintEvent(self.print_event_callback_id)  # type: ignore
            self.print_event_callback_id = -1

        if self.init_agent_callback_id != -1:
            self.kernel.UnregisterForAgentEvent(self.init_agent_callback_id)  # type: ignore
            self.init_agent_callback_id = -1

        for name, connector in self.connectors.items():
            logger.info(f"Calling disconnect() on connector {name}...")
            connector.disconnect()

        self.connected = False

    def reset(self):
        """Will destroy the current agent and create + source a new one"""
        self._destroy_soar_agent()
        self._create_soar_agent()
        self.connect()

    def full_init(self, excise_productions=False):
        """Initialize everything about the agent; production exicision is only
        performed if excise_productions is True."""
        if self.agent is None:
            raise ValueError("Cannot do full_init because agent is None")
        logger.info("Re-initializing Soar agent...")
        self.execute_command("init-soar", True)
        self.execute_command("smem --clear", True)
        self.execute_command("epmem --init", True)
        self.execute_command("svs S1.scene.clear", True)
        if excise_productions:
            self.execute_command("production excise --all", True)
        self.source_agent()
        self.apply_watch_level()

    def kill(self):
        """Will destroy the current agent + kernel, cleans up everything"""
        self._destroy_soar_agent()
        logger.info("Shutting down Soar kernel...")
        self.kernel.Shutdown()  # type: ignore
        self.kernel = None

    #### Internal Methods
    def _run_thread(self, steps: Optional[int]):
        if steps is None:
            self.execute_command("run", True)  # type: ignore
        else:
            self.execute_command(f"run {steps}", True)  # type: ignore
        self.is_running = False

    def _create_soar_agent(self):
        logger.info("Creating/connecting Soar agent...")
        self.log_writer = None
        if self.config.enable_log:
            try:
                self.log_writer = open(self.config.log_filename, "w")
            except:
                message = "ERROR: Cannot open log file " + self.config.log_filename
                self.print_handler(message)
                logger.error(message)

        if self.config.remote_connection:
            if self.config.agent_name:
                self.agent = self.kernel.GetAgent(self.config.agent_name)  # type: ignore
                if self.agent is None:
                    raise ValueError(
                        f"Error: Connected to remote kernel, but could not find specified agent '{self.config.agent_name}'"
                    )
            else:
                self.agent = self.kernel.GetAgentByIndex(0)  # type: ignore
                if self.agent is None:
                    raise ValueError(
                        "Error: Connected to remote kernel, but could not find any agents"
                    )
                print(
                    f"Connected to remote kernel. Using first agent found: '{self.agent.GetAgentName()}'"
                )
            if self.config.source_remote_agent:
                self.source_agent()
        else:
            self.agent = self.kernel.CreateAgent(self.config.agent_name)  # type: ignore
            self.source_agent()

        if self.config.spawn_debugger:
            self.spawn_debugger()

        self.apply_watch_level()

    def apply_watch_level(self):
        if self.agent is None:
            raise ValueError("Cannot apply watch level because agent is None")
        self.execute_command(f"w {self.config.watch_level}", True)

    def spawn_debugger(self):
        logger.info(f"Spawning debugger...")
        success = self.agent.SpawnDebugger()  # type: ignore
        if not success:
            self.print_handler("Failed to spawn debugger")
        logger.info(f"Debugger spawned: {success}")
        return success

    def kill_debugger(self):
        logger.info(f"Killing debugger...")
        success = self.agent.KillDebugger()  # type: ignore
        if not success:
            self.print_handler("Failed to kill debugger")
        logger.info(f"Debugger killed: {success}")
        return success

    def source_agent(self):
        logger.info("Sourcing agent...")
        self.execute_command("smem --set database memory", True)  # type: ignore
        self.execute_command("epmem --set database memory", True)  # type: ignore

        if self.config.smem_source != None:
            if self.config.source_output != "none":
                self.print_handler("------------- SOURCING SMEM ---------------")
            result = self.execute_command(f"source {{{self.config.smem_source.as_posix()}}}")  # type: ignore
            if self.config.source_output == "full":
                self.print_handler(result)
            elif self.config.source_output == "summary":
                self._summarize_smem_source(result)
            if not self.agent.GetLastCommandLineResult():  # type: ignore
                raise ValueError(
                    f"Error sourcing smem file: {self.config.smem_source}\n{result}"
                )

        if self.config.agent_source != None:
            if self.config.source_output != "none":
                self.print_handler("--------- SOURCING PRODUCTIONS ------------")
            if self.config.source_output != "none":
                verbose = " -v"
            else:
                verbose = ""
            result = self.execute_command(  # type: ignore
                f"source {{{self.config.agent_source.as_posix()}}} {verbose}", True
            )
            if self.config.source_output == "full":
                self.print_handler(result)
            elif self.config.source_output == "summary":
                self._summarize_source(result)
            if not self.agent.GetLastCommandLineResult():  # type: ignore
                raise ValueError(
                    f"Error sourcing production file: {self.config.agent_source}\n{result}"
                )
        else:
            self.print_handler("agent_source not specified, no rules are being sourced")
            logger.warning("agent_source not specified, no rules are being sourced")

    # Prints a summary of the smem source command instead of every line (source_output = summary)
    def _summarize_smem_source(self, printout: str):
        summary_lines = []
        n_added = 0
        for line in printout.split("\n"):
            if line == "Knowledge added to semantic memory.":
                n_added += 1
            else:
                summary_lines.append(line)
        summary_lines.append(f"Knowledge added to semantic memory. [{n_added} times]")
        summary = "\n".join(summary_lines)
        self.print_handler(summary)
        logger.info(summary)

    # Prints a summary of the agent source command instead of every line (source_output = summary)
    def _summarize_source(self, printout: str):
        summary_lines = []
        for line in printout.split("\n"):
            if line.startswith("Sourcing"):
                continue
            if line.startswith("warnings is now"):
                continue
            # Line is only * or # characters
            if all(c in "#* " for c in line):
                continue
            summary_lines.append(line)
        summary = "\n".join(summary_lines)
        self.print_handler(summary)
        logger.info(summary)

    def _on_init_soar(self):
        for name, connector in self.connectors.items():
            logger.info(f"Calling on_init_soar on connector {name}...")
            connector.on_init_soar()

    def _destroy_soar_agent(self):
        logger.info("Stopping Soar agent...")
        self.stop()
        while self.is_running:
            sleep(0.01)
        self._on_init_soar()
        self.disconnect()
        if self.config.spawn_debugger:
            logger.info("Killing debugger...")
            self.agent.KillDebugger()  # type: ignore
        if not self.config.remote_connection:
            logger.info("Destroying agent...")
            self.kernel.DestroyAgent(self.agent)  # type: ignore
        self.agent = None
        if self.log_writer is not None:
            logger.info("Closing log file...")
            self.log_writer.close()
            self.log_writer = None

    @staticmethod
    def _init_agent_handler(eventID, self: "SoarClient", info):
        try:
            self._on_init_soar()
        except:
            message = "ERROR IN INIT AGENT\n" + traceback.format_exc()
            self.print_handler(message)
            logger.error(message)

    @staticmethod
    def _run_event_handler(eventID, self: "SoarClient", agent, phase):
        if eventID == sml.smlEVENT_BEFORE_INPUT_PHASE:
            self._on_input_phase(agent.GetInputLink())

    def _on_input_phase(self, input_link):
        try:
            if self.queue_stop:
                logger.info("Stop requested. Stopping agent...")
                self.agent.StopSelf()  # type: ignore
                self.queue_stop = False

            for name, connector in self.connectors.items():
                logger.debug(f"Calling on_input_phase() on connector {name}...")
                connector.on_input_phase(input_link)

            if self.agent.IsCommitRequired():  # type: ignore
                logger.debug("Committing WM changes...")
                self.agent.Commit()  # type: ignore
        except:
            message = "ERROR IN INPUT PHASE\n" + traceback.format_exc()
            self.print_handler(message)
            logger.error(message)

    @staticmethod
    def _print_event_handler(eventID, self: "SoarClient", agent, message: str):
        try:
            logger.info(f"Agent print event: {message.strip()}")
            if self.config.write_to_stdout:
                message = message.strip()
                self.print_handler(message)
            if self.log_writer:
                self.log_writer.write(message)
                self.log_writer.flush()
            for ph in self.print_event_handlers:
                ph(message)
        except:
            message = "ERROR IN PRINT HANDLER\n" + traceback.format_exc()
            self.print_handler(message)
            logger.error(message)
