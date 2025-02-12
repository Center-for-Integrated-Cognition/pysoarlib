from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

DEFAULT_AGENT_NAME = "soaragent"


@dataclass
class Config:
    f"""
    agent_name = [string] (default=None if using remote connection, otherwise "{DEFAULT_AGENT_NAME}")
        Name to give the SML Agent when it is created

    agent_source = [filename] (default=None)
        Soar file to source when the agent is created

    smem_source = [filename] (default=None)
        Soar file with smem add commands to source the agent is created

    source_output = full|summary|none (default=summary)
        Determines how much output is printed when sourcing files

    watch_level = [int] (default=1)
        The watch level to use (controls amount of info printed, 0=none, 5=all)

    start_running = true|false (default=false)
        If true, will immediately start the agent running

    spawn_debugger = true|false (default=false)
        If true, will spawn the java soar debugger

    write_to_stdout = true|false (default=false)
        If true, will print all soar output to the given print_handler (default is python print)

    enable_log = true|false
        If true, will write all soar output to a file given by log_filename

    log_filename = [filename] (default = agent-log.txt)
        Specify the name of the log file to write

    remote_connection = true|false (default=false)
        If true, will connect to a remote kernel instead of creating a new one

    source_remote_agent = true|false (default=false)
        If remote_connection is true, setting this to true will source the
        remote agent with the agent source, smem source, etc.
        Otherwise, assumes that the remote agent is already sourced.

    label_dialog_source = true|false (default=false)
        If true, will label messages in chat gui with source (Agent, User)

    connect_language_model = true|false (default=false)
        If true, will establish connection with language model for I/O

    use_time_connector = true|false (default=false)
        If true, will create a TimeConnector to add time info the the input-link
        See the Readme or TimeConnector.py for additional settings to control its behavior
    """

    agent_name: Optional[str] = None
    agent_source: Optional[Path] = None
    smem_source: Optional[Path] = None
    source_output: Literal["summary"] | Literal["none"] | Literal["full"] = "summary"
    watch_level: Literal[1] | Literal[2] | Literal[3] | Literal[4] | Literal[5] = 1
    remote_connection: bool = False
    source_remote_agent: bool = False
    label_dialog_source: bool = False
    connect_language_model: bool = False
    spawn_debugger: bool = False
    start_running: bool = False
    write_to_stdout: bool = False
    enable_log: bool = False
    log_filename: str = "agent-log.txt"
    use_time_connector: bool = False

    def __post_init__(self):
        if not self.remote_connection and not self.agent_name:
            self.agent_name = "soaragent"
