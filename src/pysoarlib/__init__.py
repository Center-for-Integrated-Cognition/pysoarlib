"""Helper classes and functions for creating a soar agent and working with SML

Depends on the Python_sml_ClientInterface, so make sure that SOAR_HOME is on the PYTHONPATH

SoarClient and AgentConnector are used to create an agent
WMInterface is a standardized interface for adding/removing structures from working memory
SoarWME is a wrapper for creating working memory elements
SVSCommands will generate svs command strings for some common use cases

Also adds helper methods to the Identifier class to access children more easily
(See IdentifierExtensions)

"""

from pysoarlib.util.sml import sml

__all__ = [
    "WMInterface",
    "SoarWME",
    "SVSCommands",
    "AgentConnector",
    "SoarClient",
    "TimeConnector",
    "LMConnector",
]

# Extend the sml Identifier class definition with additional utility methods
from pysoarlib.IdentifierExtensions import *

# PyLance says: these members are not known, so they cannot be assigned. So we ignore types for now.
sml.Identifier.GetChildString = get_child_str  # type: ignore
sml.Identifier.GetChildInt = get_child_int  # type: ignore
sml.Identifier.GetChildFloat = get_child_float  # type: ignore
sml.Identifier.GetChildId = get_child_id  # type: ignore
sml.Identifier.GetAllChildIds = get_all_child_ids  # type: ignore
sml.Identifier.GetAllChildValues = get_all_child_values  # type: ignore
sml.Identifier.GetAllChildWmes = get_all_child_wmes  # type: ignore
sml.Identifier.__lt__ = (  # type: ignore
    lambda self, other: self.GetIdentifierSymbol() < other.GetIdentifierSymbol()
)

from pysoarlib.WMInterface import WMInterface
from pysoarlib.SoarWME import SoarWME
from pysoarlib.SVSCommands import SVSCommands
from pysoarlib.AgentConnector import AgentConnector
from pysoarlib.SoarClient import SoarClient
from pysoarlib.TimeConnector import TimeConnector

# only works if langchain_openai is installed
try:
    from pysoarlib.connectors.language_model.LMConnector import LMConnector
except ImportError:
    pass
