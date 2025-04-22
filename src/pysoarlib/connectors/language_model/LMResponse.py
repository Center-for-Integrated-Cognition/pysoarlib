""" Data structures for LM response (WMInterface)

    Classes for storing LM response
"""

import json

#from pysoarlib.WMInterface import WMInterface
from pysoarlib.connectors.Response import Response




#class LMResponse(WMInterface):
class LMResponse(Response):
    def __init__(self, query, results, sequence_number = 0):
        Response.__init__(self, query, results)
        #CommunicatorResponse.__init__(self, connector, query, results)
        #self.connector = connector
        self.results = results
        self.sequence_number = sequence_number
        # self.response = results.response
        # self.response_type = results.response_type
        # self.propability = results.probability


    #def add_json_to_soar_input(self, result_wme, result):
    def add_json_to_soar_input(self, parent_id, json_object):
        print(type(json_object))
        node_wmes = {}

        if isinstance(json_object, dict):
            for key, value in json_object.items():
                self.add_json_to_soar_attribute(parent_id, key, value, node_wmes)
        # elif isinstance(json_object, list):
        #     new_id = parent_id.CreateIdWME("weird")
        #     for item in json_object:
        #         self.add_json_to_soar_attribute(new_id, 'item', item)
        else:
            print("Error root JSONmust be a dict")
            raise ValueError("The root JSON object must be a dictionary")

    def add_json_to_soar_attribute(self, parent_id, attribute, json_object, node_wmes):
        if isinstance(json_object, dict):
            new_id = parent_id.CreateIdWME(attribute)
            for key, value in json_object.items():
                self.add_json_to_soar_attribute(new_id, key, value, node_wmes)
        elif isinstance(json_object, list):
            attr = attribute.rstrip("s") #plural set
            #new_id = parent_id.CreateIdWME(attribute)
            for item in json_object:
                self.add_json_to_soar_attribute(parent_id, attr, item, node_wmes)
        elif isinstance(json_object, bool):
            # Convert booleans to strings 'true' or 'false'
            parent_id.CreateStringWME(attribute, str(json_object).lower())
        elif isinstance(json_object, int):
            parent_id.CreateIntWME(attribute, json_object)
        elif isinstance(json_object, float):
            parent_id.CreateFloatWME(attribute, json_object)
        elif isinstance(json_object, str):
            if attribute == "node":
                node_wmes[json_object] = parent_id
            if "argument" in attribute and "node" in json_object:
                if node_wmes[json_object]:
                    parent_id.CreateSharedIdWME(attribute, node_wmes[json_object])
                else:
                    print("Error refered to node not found:" + json_object)
            else:
                parent_id.CreateStringWME(attribute, json_object)
        # elif json_object is None:
        #     parent_id.CreateStringWME(attribute, 'nil')
        # else:
        #     parent_id.CreateStringWME(attribute, str(json_object))
        
    # def _add_to_wm_impl(self, parent_id):
    #     """  For now, LMResult only allows for one result. """
    #     self.identifier = parent_id.CreateIdWME("responses")
    #     results_count = len(self.results)
    #     self.identifier.CreateIntWME("result-count", results_count)
    #     self.identifier.CreateIntWME("sequence-number", self.sequence_number)
    #     for result in self.results:
    #         result_wme = self.identifier.CreateIdWME("result")
    #         result_wme.CreateFloatWME("probability", result.probability)
    #         result_wme.CreateIntWME("order", int(result.order))
    #         match result.response_type:
    #             case "string":
    #                 result_wme.CreateStringWME("response", result.response)
    #             case "int":
    #                 result_wme.CreateIntWME("response", int(result.response))
    #             case "float":
    #                 result_wme.CreateFloatWME("response", float(result.response))
    #             case "json":
    #                 response_wme = result_wme.CreateIdWME("response")
    #                 self.add_json_to_soar_input(response_wme, result.response)

    def _add_to_wm_impl(self, results_wme):
        """  For now, LMResult only allows for one result. """
        results_count = len(self.results)
        results_wme.CreateIntWME("result-count", results_count)
        for result in self.results:
            result_wme = results_wme.CreateIdWME("result")
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
