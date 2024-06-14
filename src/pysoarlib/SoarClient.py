from pathlib import Path
from threading import Thread
import traceback
from time import sleep
from typing import Optional

from pysoarlib.util.sml import sml
from pysoarlib.Config import Config
from pysoarlib.TimeConnector import TimeConnector


class SoarClient:
    """A wrapper class for creating and using a soar SML Agent"""

    def __init__(self, print_handler=None, config: Config = Config()):
        """Will create a soar kernel and agent

        print_handler determines how output is printed, defaults to python print

        Note: Still need to call connect() to register event handlers
        """

        if print_handler is not None:
            self.print_handler = print_handler
        else:
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
            self.kernel = sml.Kernel.CreateRemoteConnection()
        else:
            self.kernel = sml.Kernel.CreateKernelInNewThread()
            self.kernel.SetAutoCommit(False)

        if self.config.use_time_connector:
            self.add_connector("time", TimeConnector(self, **self.config.__dict__))
        self._create_soar_agent()

    def add_connector(self, name, connector):
        """Adds an AgentConnector to the agent"""
        self.connectors[name] = connector

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

    def start(self, steps: Optional[int] = None):
        """Will start the agent (uses another thread, so non-blocking)"""
        if self.is_running:
            return

        self.is_running = True
        thread = Thread(
            target=SoarClient._run_thread, name="Soar run thread", args=(self, steps)
        )
        thread.start()

    def stop(self):
        """Tell the running thread to stop

        Note: Non-blocking, agent may run for a bit after this call finishes"""
        self.queue_stop = True

    def execute_command(self, cmd, print_res=False):
        """Execute a soar command and return result,
        write output to print_handler if print_res is True"""
        result = self.agent.ExecuteCommandLine(cmd).strip()  # type: ignore
        if print_res:
            self.print_handler(cmd)
            self.print_handler(result)
        return result

    def connect(self):
        """Register event handlers for agent and connectors"""
        if self.connected:
            return

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

        for connector in self.connectors.values():
            connector.connect()

        self.connected = True

        if self.config.start_running:
            self.start()

    def disconnect(self):
        """Unregister event handlers for agent and connectors"""
        if not self.connected:
            return

        if self.run_event_callback_id != -1:
            self.agent.UnregisterForRunEvent(self.run_event_callback_id)  # type: ignore
            self.run_event_callback_id = -1

        if self.print_event_callback_id != -1:
            self.agent.UnregisterForPrintEvent(self.print_event_callback_id)  # type: ignore
            self.print_event_callback_id = -1

        if self.init_agent_callback_id != -1:
            self.kernel.UnregisterForAgentEvent(self.init_agent_callback_id)  # type: ignore
            self.init_agent_callback_id = -1

        for connector in self.connectors.values():
            connector.disconnect()

        self.connected = False

    def reset(self):
        """Will destroy the current agent and create + source a new one"""
        self._destroy_soar_agent()
        self._create_soar_agent()
        self.connect()

    def kill(self):
        """Will destroy the current agent + kernel, cleans up everything"""
        self._destroy_soar_agent()
        self.kernel.Shutdown()  # type: ignore
        self.kernel = None

    #### Internal Methods
    def _run_thread(self, steps: Optional[int]):
        if steps is None:
            self.agent.ExecuteCommandLine("run")  # type: ignore
        else:
            self.agent.ExecuteCommandLine(f"run {steps}")  # type: ignore
        self.is_running = False

    def _create_soar_agent(self):
        self.log_writer = None
        if self.config.enable_log:
            try:
                self.log_writer = open(self.config.log_filename, "w")
            except:
                self.print_handler(
                    "ERROR: Cannot open log file " + self.config.log_filename
                )

        if self.config.remote_connection:
            self.agent = self.kernel.GetAgentByIndex(0)  # type: ignore
        else:
            self.agent = self.kernel.CreateAgent(self.config.agent_name)  # type: ignore
            self._source_agent()

        if self.config.spawn_debugger:
            success = self.agent.SpawnDebugger(self.kernel.GetListenerPort())  # type: ignore
            if not success:
                self.print_handler("Failed to spawn debugger")

        self.agent.ExecuteCommandLine(f"w {self.config.watch_level}")

    def _source_agent(self):
        self.agent.ExecuteCommandLine("smem --set database memory")  # type: ignore
        self.agent.ExecuteCommandLine("epmem --set database memory")  # type: ignore

        if self.config.smem_source != None:
            if self.config.source_output != "none":
                self.print_handler("------------- SOURCING SMEM ---------------")
            result = self.agent.ExecuteCommandLine(f"source {{{self.config.smem_source.as_posix()}}}")  # type: ignore
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
            result = self.agent.ExecuteCommandLine(  # type: ignore
                f"source {{{self.config.agent_source.as_posix()}}} -v"
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

    # Prints a summary of the smem source command instead of every line (source_output = summary)
    def _summarize_smem_source(self, printout: str):
        summary = []
        n_added = 0
        for line in printout.split("\n"):
            if line == "Knowledge added to semantic memory.":
                n_added += 1
            else:
                summary.append(line)
        self.print_handler("\n".join(summary))
        self.print_handler(f"Knowledge added to semantic memory. [{n_added} times]")

    # Prints a summary of the agent source command instead of every line (source_output = summary)
    def _summarize_source(self, printout: str):
        summary = []
        for line in printout.split("\n"):
            if line.startswith("Sourcing"):
                continue
            if line.startswith("warnings is now"):
                continue
            # Line is only * or # characters
            if all(c in "#* " for c in line):
                continue
            summary.append(line)
        self.print_handler("\n".join(summary))

    def _on_init_soar(self):
        for connector in self.connectors.values():
            connector.on_init_soar()

    def _destroy_soar_agent(self):
        self.stop()
        while self.is_running:
            sleep(0.01)
        self._on_init_soar()
        self.disconnect()
        if self.config.spawn_debugger:
            self.agent.KillDebugger()  # type: ignore
        if not self.config.remote_connection:
            self.kernel.DestroyAgent(self.agent)  # type: ignore
        self.agent = None
        if self.log_writer is not None:
            self.log_writer.close()
            self.log_writer = None

    @staticmethod
    def _init_agent_handler(eventID, self: "SoarClient", info):
        try:
            self._on_init_soar()
        except:
            self.print_handler("ERROR IN INIT AGENT")
            self.print_handler(traceback.format_exc())

    @staticmethod
    def _run_event_handler(eventID, self: "SoarClient", agent, phase):
        if eventID == sml.smlEVENT_BEFORE_INPUT_PHASE:
            self._on_input_phase(agent.GetInputLink())

    def _on_input_phase(self, input_link):
        try:
            if self.queue_stop:
                self.agent.StopSelf()  # type: ignore
                self.queue_stop = False

            for connector in self.connectors.values():
                connector.on_input_phase(input_link)

            if self.agent.IsCommitRequired():  # type: ignore
                self.agent.Commit()  # type: ignore
        except:
            self.print_handler("ERROR IN RUN HANDLER")
            self.print_handler(traceback.format_exc())

    @staticmethod
    def _print_event_handler(eventID, self: "SoarClient", agent, message: str):
        try:
            if self.config.write_to_stdout:
                message = message.strip()
                self.print_handler(message)
            if self.log_writer:
                self.log_writer.write(message)
                self.log_writer.flush()
            for ph in self.print_event_handlers:
                ph(message)
        except:
            self.print_handler("ERROR IN PRINT HANDLER")
            self.print_handler(traceback.format_exc())
