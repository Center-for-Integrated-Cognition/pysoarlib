""" 
    LM Result structure
"""


class LMResult:
    def __init__(self, response, response_type, probability, order):
        self.response = response
        self.response_type = response_type
        self.probability = probability
        self.order = order