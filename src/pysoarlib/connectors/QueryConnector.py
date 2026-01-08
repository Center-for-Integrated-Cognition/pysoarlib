""" Generic Base Class for query based connectors (e.g., LLM, database)

Adds helper functions for processing queries, storing and removing queries
Queries have sequence-numbers for each QueryConnector
"""

import json
import traceback

from pysoarlib import AgentConnector
from pysoarlib.connectors.Query import Query
from pysoarlib.util.sml import sml
from pysoarlib.util.soar_identifier_to_json import soar_identifier_to_json
from pysoarlib.util.soar_identifier_to_json import soar_identifier_to_json_limited

class QueryConnector(AgentConnector):
    """Base Class for Query Connectors based on agent connector

    Look at LMConnector for an example of an QueryConnector used in practice
    """
    def __init__(self, client):
        AgentConnector.__init__(self, client)

        #self.communicator = communicator
        # self.root_id = None
        self.response = None
        self.responses = {}
        self.needs_setup = True

        # new output commands
        # Soar commands for connector queries area added
        # for each connector when the connector is registere
        # with the Communicator
        #self.add_output_command("delete-response")

       # """  A dictionary of connector wmes  """
       # self.connector_names = self.communicator.connectors.keys()
       # self.connector_ids = {}


    # def on_init_soar(self):
    #     # print("on_init_soar")
    #     """  Clear out any previous structures on the input link  """
    #     for name in self.connector_names:
    #         root_id = self.connector_ids.get(name)
    #         if root_id != None:
    #             root_id.DestroyWME()
    #             self.connector_ids[name] = None
    #             """ This is needed to be able to re-start. """
    #             self.needs_setup = True
##################################33QQQQQQQQQQQQQQQQQQQQQq

    # def on_input_phase(self, input_link):
    #     """
    #     on input phase add to WM input-link lm id (if doesn't exist) and response if it does
    #     """
    #     if self.lm_id == None:
    #         self.lm_id = input_link.CreateIdWME("language-model")

    #     if self.response != None and not self.response.is_added():
    #         self.response.add_to_wm(self.lm_id)


    # def on_output_event(self, command_name, root_id):
    #     """
    #     Handle output link events, commands for LM requets
    #     """
    #     if command_name == "language-model":#"lm-request":
    #         if self.response != None:
    #             self.response.remove_from_wm()
    #             self.response = None

    #         self.process_lm_request(root_id)
    #     if command_name == "delete-lm-response":#"lm-request":
    #         if self.response != None:
    #             self.response.remove_from_wm()
    #             self.response = None
    #         root_id.CreateStringWME("status", "complete")


###########################33QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
    # def on_input_phase(self, input_link):
    #     """
    #     On input phase add a WME for the response's connector to input-link (if doesn't exist)
    #     Then post the details of the response
    #     """
    #     # print("on_input_phase")
    #     # print(input_link.GetValueAsString())

    #     """  Setup the input link structure for all connectors  """
    #     """  For now, the structure is I2.<connector-name>.responses  """
    #     """  Then each response will be added under that  """
    #     if self.needs_setup:
    #         for name in self.connector_names:
    #             connector_wme = input_link.FindByAttribute(name, 0)
    #             if connector_wme is None:
    #                 connector_id = input_link.CreateIdWME(name)
    #                 id = connector_id.GetValueAsString()
    #                 print("Created a connector id '{}' for connector '{}'".format(id, name))
    #                 responses_id = connector_id.CreateIdWME("responses")
    #                 id = responses_id.GetValueAsString()
    #                 # print("Created a responses id '{}' for connector '{}'".format(id, name))
    #                 self.connector_ids[name] = connector_id
    #         self.needs_setup = False

    #     if self.response != None: # and not self.response.is_added():
    #         """  Create a root wme for this connector if not already there  """
    #         name = self.response.name
    #         root_id = self.connector_ids.get(name) # Should never by None
    #         self.response.add_to_wm(root_id)
    #         """  Forget it to be clear for next input phase  """
    #         self.response = None


    # def on_output_event(self, command_name, root_id):
    #     """
    #     Handle output link events, commands for LM requests
    #     """
    #     # print(root_id.GetValueAsString())
    #     id = root_id.GetValueAsString()
    #     # print("on_output_event called, root_id = '{}'".format(id))
    #     print("SoarConnector output command: " + command_name)
    #     match command_name:
    #         case "delete-response":
    #             connector_name = root_id.FindByAttribute("connector", 0).ConvertToStringElement().GetValue()
    #             # print("delete-response received from connector {}.".format(connector_name))
    #             sequence_number = root_id.FindByAttribute("sequence-number", 0).ConvertToIntElement().GetValue()
    #             print("Connector: {}.".format(connector_name))
    #             print("Deleting response {}".format(sequence_number))
    #             """  Tell the connector to delete that response  """
    #             connector = self.communicator.get_connector(connector_name)

    #             connector.delete_response(sequence_number)
    #         case "send-response":
    #             print("Error should never get send-response in SoarConnector output handler")
    #             pass
    #         case command_name: #TODO this is dangerous for other connectors that are not doing queries
    #             print("Query command received for connector {}.".format(command_name))
    #             self.process_query_command(command_name, root_id)
    #     """  Mark the command as complete  """
    #     root_id.CreateStringWME("status", "complete")


    def remember_response(self, response):
        sequence_number = response.sequence_number
        self.responses[sequence_number] = response

    def delete_response(self, sequence_number):
        """ Don't try to delete it if it's not there """
        if sequence_number in self.responses:
            response = self.responses[sequence_number]
            response.remove_from_wm()
            self.responses.pop(sequence_number)
        else:
            print("Error trying to delete sequence number " + str(sequence_number))

    def process_query_command(self, root_id):
        """
        Processes query from output-link command
        result is query structure
        """

        """  Parse the query  """
        query_id = root_id.FindByAttribute("query", 0).ConvertToIdentifier()
        type = query_id.FindByAttribute("type", 0).GetValueAsString()
        # print("Query type = " + type)

        #Get request type
        request_type = query_id.FindByAttribute("type", 0).GetValueAsString()
        # print(request_type)
        if not request_type:
            root_id.CreateStringWME("status", "error")
            root_id.CreateStringWME("error-info", "query has no type")
            self.client.print_handler("Error - outputlink query has no type")
            return

        #Use sequence-number as unique id of response
        sequence_number = query_id.FindByAttribute("sequence-number", 0).ConvertToIntElement().GetValue()
        # print(sequence_number)

        #Get argument count
        argument_count = query_id.FindByAttribute("argument-count", 0).ConvertToIntElement().GetValue()
        # print(argument_count)
        context = None
        if query_id.FindByAttribute("context", 0):
            context = query_id.FindByAttribute("context", 0).ConvertToIdentifier()

        arguments = []
        i = 1
        while (i <= argument_count):
            argnum = "argument" + str(i)
            arg = query_id.FindByAttribute(argnum, 0)
            arg_type = arg.GetValueType()
            argument = ""
            match arg_type:
                case "int":
                    argument = arg.ConvertToIntElement().GetValue()
                case "string":
                    argument = arg.GetValueAsString()
                case "double":
                    argument = arg.ConvertToFloatElement().GetValue()
                case "id":
                    # argument = arg.ConvertToIdentifier()
                    #hack for now, make option in config to specify exclusions and depth limit
                    if request_type == "translate-hlg-result" and i == 3:
                        argument = json.dumps(soar_identifier_to_json_limited(arg.ConvertToIdentifier(), exclusions=["argument1", "argument2", "argument3", "argument4", "node-result"], depth_limit=2), indent=4)
                    else:
                        argument = json.dumps(soar_identifier_to_json(arg.ConvertToIdentifier()), indent=4)
            arguments.append(argument)
            i+=1
        # print(arguments)

        """  Create Query """
        query = Query(sequence_number, request_type, arguments, context)
        view = "Query {}: {}, {}, {}, {}".format(request_type, sequence_number, argument_count, arguments, context)
        print(view)

        return query

        # """  Give it to the Communicator  """
        # self.response = self.communicator.process_query(query)
