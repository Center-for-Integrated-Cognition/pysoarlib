from pathlib import Path
from pysoarlib.AgentConnector import AgentConnector
from pysoarlib.Config import Config
from pysoarlib.SoarClient import SoarClient
from pysoarlib.SoarWME import SoarWME

CUR_DIR = Path(__file__).parent
TEST_AGENT = CUR_DIR / "test-agent.soar"


class SimpleConnector(AgentConnector):
    def __init__(self, client):
        AgentConnector.__init__(self, client)
        self.add_output_command("increase-number")
        self.num = SoarWME("number", 0)

    def on_input_phase(self, input_link):
        if not self.num.is_added():
            self.num.add_to_wm(input_link)
        else:
            self.num.update_wm()

    def on_init_soar(self):
        self.num.remove_from_wm()

    def on_output_event(self, command_name, root_id):
        if command_name == "increase-number":
            self.process_increase_command(root_id)

    def process_increase_command(self, root_id):
        number = root_id.GetChildInt("number")
        if number:
            self.num.set_value(self.num.val + number)
        root_id.AddStatusComplete()


config = Config(
    agent_name="simple",
    agent_source=TEST_AGENT,
    source_output="summary",
    spawn_debugger=False,
    write_to_stdout=True,
)
client = SoarClient(config)
client.add_connector("simple", SimpleConnector(client))
client.connect()

client.execute_command("run 12")

client.kill()
