import logging
from pprint import pprint

import requests

logger = logging.getLogger(__name__)


# Respect the method name for run_sparql_on with enums
def get_identifierorg_uri(identifier):
    """
    return the identifier.org uri for the given identifier
    such that it matches what GO has stored for the URI.  This
    means using http vs. https and using the stored prefix (for
    flybase this is 'flybase' vs. 'fb' in identifiers.org)

    :param identifier: the identifier to convert to an identifier.org uri
    :return: the identifier.org uri as specified in Noctua
    """
    if identifier.startswith("FB:"):
        uri = "http://identifiers.org/" + "flybase/" + identifier.split(":")[1]
    else:
        uri = "http://identifiers.org/" + identifier.split(":")[0].lower() +"/" + identifier
    return uri
