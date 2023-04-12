import logging
from pprint import pprint
import json
import urllib.request

logger = logging.getLogger(__name__)


# have to remap prefixes from prefixmaps in order to match the prefixes in Minerva
def remap_prefixes(cmap):
    response = urllib.request.urlopen("https://raw.githubusercontent.com/ExposuresProvider/cam-pipeline/kg-tsv/supplemental-namespaces.json")
    data = json.loads(response.read().decode())
    for k, v in data.items():
        cmap[k] = v
    cmap["MGI"] = "http://identifiers.org/mgi/MGI:"
    cmap["WB"] = "http://identifiers.org/wormbase/"
    return cmap

