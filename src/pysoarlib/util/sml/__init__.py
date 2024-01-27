"""Import sml from here so that users get a nicer error message if they don't have it in their path"""

import sys

try:
    import Python_sml_ClientInterface as sml
except ImportError:
    raise ImportError(
        "Could not import the Python SML client interface. Make sure the Soar's root directory (SOAR_HOME) is added to the PYTHONPATH environment variable. It currently contains:\n"
        + "\n".join([f"  '{p}'" for p in sys.path])
    )
