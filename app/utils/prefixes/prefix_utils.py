import logging
from pprint import pprint
import json
import urllib.request

logger = logging.getLogger(__name__)


# Respect the method name for run_sparql_on with enums
def remap_prefixes(cmap):
    data = json.loads(urllib.request.urlopen("https://github.com/ExposuresProvider/cam-pipeline/blob/kg-tsv/supplemental-namespaces.json").read().decode())
    for k, v in data.items():
        cmap[k] = v
    return cmap

