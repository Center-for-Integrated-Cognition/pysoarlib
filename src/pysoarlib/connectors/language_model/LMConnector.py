from pysoarlib.AgentConnector import AgentConnector
#from LanguageModelConnector.LLM import LLM
from pysoarlib.connectors.language_model.LLM import LLM


#from Communicator.ExternalConnector import ExternalConnector


class LMConnector(AgentConnector):
    def __init__(self, client, world_connector, model = "gpt-4o"):
        AgentConnector.__init__(self, client)

        #new output commands
        self.add_output_command("language-model")
        self.add_output_command("delete-lm-response")
        #self.add_output_command("lm-request")
       
        self.response = None
        self.temperature = 0
        self.model = model
        self.lm = LLM(world_connector, self.temperature, self.model)
        

        self.lm_id = None
        self.lm_failsafe = 0 #to prevent accidental exhaustion of tokens

    def on_init_soar(self):
        """
        on init remove existing responses, input-link WM id if they already exist
        """
        if self.response != None:
            self.response.remove_from_wm()
            self.response = None

        if self.lm_id != None:
            self.lm_id.DestroyWME()
            self.lm_id = None

    def on_input_phase(self, input_link):
        """
        on input phase add to WM input-link lm id (if doesn't exist) and response if it does
        """
        if self.lm_id == None:
            self.lm_id = input_link.CreateIdWME("language-model")

        if self.response != None and not self.response.is_added():
            self.response.add_to_wm(self.lm_id)


    def on_output_event(self, command_name, root_id):
        """
        Handle output link events, commands for LM requets
        """
        if command_name == "language-model":#"lm-request":
            if self.response != None:
                self.response.remove_from_wm()      
                self.response = None

            self.process_lm_request(root_id)
        if command_name == "delete-lm-response":#"lm-request":
            if self.response != None:
                self.response.remove_from_wm()      
                self.response = None
            root_id.CreateStringWME("status", "complete")

   
    def process_lm_request(self, root_id):
        """
        Processes lm request getting parameters from output-link command
        result is new response created (that will be added on input-phase)
        """
       
        #Get request type
        query_id = root_id.GetChildId("query")
        request_type = query_id.FindByAttribute("type", 0).GetValueAsString()
        if not request_type:
            root_id.CreateStringWME("status", "error")
            root_id.CreateStringWME("error-info", "lm-request has no type")
            self.client.print_handler("LMConnector: Error - lm-request has no type")
            return
       
        #Use wme as unique id of response (maybe not necessary)
        #root_wme = root_id.GetValueAsString()

        #Get argument count
        argument_count = query_id.FindByAttribute("argument-count", 0).ConvertToIntElement().GetValue()

        sequence_number = query_id.FindByAttribute("sequence-number", 0).ConvertToIntElement().GetValue()
       
        # arguments = []
        # i = 1
        # while (i <= argument_count):
        #     argnum = "argument" + str(i)
        #     argument = root_id.FindByAttribute(argnum, 0).GetValueAsString()
        #     arguments.append(argument)
        #     i+=1

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
                    argument = arg.ConvertToIdentifier() #need?
            arguments.append(argument)
            i+=1

        #Prevent over access of LM to avoid depleting tokens due to bug
        if self.lm_failsafe > 1000:
            print("HIT FAIL SAFETY limit stop running language model")
            return
       
        print("Running request for type " + request_type + " with argument " + str(arguments))
        #self.response = self.lm.parse_request(None,request_type, arguments, sequence_number)
        self.response = self.lm.parse_request_new(None,request_type, arguments, sequence_number)
       
        self.lm_failsafe += 1
        root_id.CreateStringWME("status", "complete")
        return
    

# class LMConnector(ExternalConnector):
#     def __init__(self, communicator, model):
#         """  Get registered with the Communicator  """
#         ExternalConnector.__init__(self, communicator, "language-model")
        
#         self.temperature = 0
#         self.model = model
#         self.lm = LLM(self, self.temperature, self.model)

#         self.lm_failsafe = 0 #to prevent accidental exhaustion of tokens

    
#     def execute(self, query):
#         """
#         Processes lm request getting parameters from output-link command
#         result is new response created (that will be added on input-phase)
#         """

#         #Prevent over access of LM to avoid depleting tokens due to bug 
#         if self.lm_failsafe > 300:
#             print("HIT FAIL SAFETY limit (300) stop running language model")
#             return
#         #print("Running request for type " + request_type + " with argument " + str(arguments))
#         response = self.lm.parse_request(query, query.type, query.arguments)

#         self.remember_response(response)
#         self.lm_failsafe += 1
#         return response
