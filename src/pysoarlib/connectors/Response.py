"""
    Data structure for a response to a query from a QueryConnector
    
    The results argument is intended to be
    a two-dimensional table where each cell
    is an attribute-value tuple.
"""

from pysoarlib import WMInterface

class Response(WMInterface):
    def __init__(self, query, results):
        WMInterface.__init__(self)
        #self.connector = connector
        #self.name = connector.name
        self.sequence_number = query.sequence_number
        self.query = query
        self.results = results
    
    def add_to_wm(self, parent_id):
        id = parent_id.GetValueAsString()
        # print("add_to_wm called, parent_id = '{}'".format(id))
        responses_id = parent_id.FindByAttribute("responses", 0).ConvertToIdentifier()
        # print("Adding response to responses_id {}".format(responses_id.GetValueAsString()))
        self.identifier = responses_id.CreateIdWME("response")
        self.identifier.CreateIntWME("sequence-number", self.sequence_number)
        self.identifier.CreateStringWME("type", self.query.type)
        self.query.add_to_wm(self.identifier)
        results_wme = self.identifier.CreateIdWME("results")
        self._add_to_wm_impl(results_wme)
    
    def remove_from_wm(self):
        if self.identifier:
            self.identifier.DestroyWME()
        self.identifier = None
