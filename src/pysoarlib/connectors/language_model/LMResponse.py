""" Data structures for LM response (WMInterface)

    Classes for storing LM response
"""

import json

from pysoarlib.WMInterface import WMInterface

# class LMResponse(WMInterface):
#     def __init__(self, id, prompt, response = "", response_type = "string", probability = 0):
#         WMInterface.__init__(self)
#         self.id = id
#         self.prompt = prompt
#         self.response = response
#         self.response_type = response_type
#         self.probability = probability

#     def _add_to_wm_impl(self, parent_id):
#         self.identifier = parent_id.CreateIdWME("response")
#         self.identifier.CreateStringWME("id", self.id)

#         if self.response_type == "string":
#             self.identifier.CreateStringWME("response", self.response)
#         elif self.response_type == "int":
#             self.identifier.CreateIntWME("response", int(self.response))
#         elif self.response_type == "float":
#             self.identifier.CreateFloatWME("response", float(self.response))
   
#     def _update_wm_impl(self):
#         pass
   
#     def _remove_from_wm_impl(self):
#         self.identifier.DestroyWME()
#         self.identifier = None



class LMResponse(WMInterface):
    def __init__(self, connector, query, results, sequence_number = 0):
        WMInterface.__init__(self)
        #CommunicatorResponse.__init__(self, connector, query, results)
        self.connector = connector
        self.results = results
        self.sequence_number = sequence_number
        # self.response = results.response
        # self.response_type = results.response_type
        # self.propability = results.probability


    #def add_json_to_soar_input(self, result_wme, result):
    def add_json_to_soar_input(self, parent_id, json_object):
        print(type(json_object))
        if isinstance(json_object, dict):
            for key, value in json_object.items():
                self.add_json_to_soar_attribute(parent_id, key, value)
        # elif isinstance(json_object, list):
        #     new_id = parent_id.CreateIdWME("weird")
        #     for item in json_object:
        #         self.add_json_to_soar_attribute(new_id, 'item', item)
        else:
            print("Error root JSONmust be a dict")
            raise ValueError("The root JSON object must be a dictionary")

    def add_json_to_soar_attribute(self, parent_id, attribute, json_object):
        if isinstance(json_object, dict):
            new_id = parent_id.CreateIdWME(attribute)
            for key, value in json_object.items():
                self.add_json_to_soar_attribute(new_id, key, value)
        elif isinstance(json_object, list):
            attr = attribute.rstrip("s") #plural set
            #new_id = parent_id.CreateIdWME(attribute)
            for item in json_object:
                self.add_json_to_soar_attribute(parent_id, attr, item)
        elif isinstance(json_object, bool):
            # Convert booleans to strings 'true' or 'false'
            parent_id.CreateStringWME(attribute, str(json_object).lower())
        elif isinstance(json_object, int):
            parent_id.CreateIntWME(attribute, json_object)
        elif isinstance(json_object, float):
            parent_id.CreateFloatWME(attribute, json_object)
        elif isinstance(json_object, str):
            parent_id.CreateStringWME(attribute, json_object)
        # elif json_object is None:
        #     parent_id.CreateStringWME(attribute, 'nil')
        # else:
        #     parent_id.CreateStringWME(attribute, str(json_object))
        
    def _add_to_wm_impl(self, parent_id):
        """  For now, LMResult only allows for one result. """
        self.identifier = parent_id.CreateIdWME("responses")
        results_count = len(self.results)
        self.identifier.CreateIntWME("result-count", results_count)
        self.identifier.CreateIntWME("sequence-number", self.sequence_number)
        for result in self.results:
            result_wme = self.identifier.CreateIdWME("result")
            result_wme.CreateFloatWME("probability", result.probability)
            result_wme.CreateIntWME("order", int(result.order))
            match result.response_type:
                case "string":
                    result_wme.CreateStringWME("response", result.response)
                case "int":
                    result_wme.CreateIntWME("response", int(result.response))
                case "float":
                    result_wme.CreateFloatWME("response", float(result.response))
                case "json":
                    response_wme = result_wme.CreateIdWME("response")
                    self.add_json_to_soar_input(response_wme, result.response)

    
    def _update_wm_impl(self):
        pass
    
    def _remove_from_wm_impl(self):
        self.identifier.DestroyWME()
        self.identifier = None
