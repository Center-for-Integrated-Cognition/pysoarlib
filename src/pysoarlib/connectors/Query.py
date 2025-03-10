"""
    Data structure for a query from Soar to the Communicator
"""

from pysoarlib import WMInterface
from pysoarlib.util.sml import sml

class Query(WMInterface):
    def __init__(self, sequence_number, type, arguments, context = None, config = None):
        WMInterface.__init__(self)
        self.sequence_number = sequence_number
        self.type = type
        self.argument_count = len(arguments)
        self.arguments = arguments
        self.context = context
        self.config = config

    def _add_to_wm_impl(self, parent_id):
        self.identifier = parent_id.CreateIdWME("query") # or x-query
        self.identifier.CreateIntWME("sequence-number", self.sequence_number)
        self.identifier.CreateStringWME("type", self.type)
        self.identifier.CreateIntWME("argument-count", self.argument_count)
        arg = 1

        for argument in self.arguments:
            argument_str =  "argument" + str(arg)

            #check for argument type
            if isinstance(argument, int):
                self.identifier.CreateIntWME(argument_str, argument)
            elif isinstance(argument, float):
                self.identifier.CreateFloatWME(argument_str, argument)
            elif isinstance(argument, sml.Identifier):
                self.identifier.CreateStringWME(argument_str, "soar_wme")
                #TODO available deep copy functionality?
            else:
                self.identifier.CreateStringWME(argument_str, argument)

            arg = arg + 1


    
    def _update_wm_impl(self):
        pass
    
    def _remove_from_wm_impl(self):
        if self.identifier:
            self.identifier.DestroyWME()
        self.identifier = None
