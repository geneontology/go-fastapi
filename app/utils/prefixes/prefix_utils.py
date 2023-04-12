import logging
import json
import urllib.request
from prefixmaps import load_context
from curies import Converter
from pprint import pprint
logger = logging.getLogger(__name__)


# have to remap prefixes from prefixmaps in order to match the prefixes in Minerva
def remap_prefixes(cmap):
    response = urllib.request.urlopen("https://raw.githubusercontent.com/ExposuresProvider/cam-pipeline/kg-tsv/supplemental-namespaces.json")
    data = json.loads(response.read().decode())
    for k, v in data.items():
        print("k: ", k)
        print("v: ", v)
        cmap[v] = k
    cmap["MGI"] = "http://identifiers.org/mgi/MGI:"
    cmap["WB"] = "http://identifiers.org/wormbase/"
    return cmap


def get_prefixes(context: str = "go"):
    context = load_context(context)
    extended_prefix_map = context.as_extended_prefix_map()
    converter = Converter.from_extended_prefix_map(extended_prefix_map)
    cmaps = converter.prefix_map
    # hacky solution to: https://github.com/geneontology/go-site/issues/2000
    cmap_remapped = remap_prefixes(cmaps)

    return cmap_remapped

