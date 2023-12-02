"""prefix utility functions."""
import logging

import curies
from curies import rewire
from prefixmaps import load_converter

logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

REWIRING = {
    "MGI": "http://identifiers.org/mgi/MGI:",
    "WB": "http://identifiers.org/wormbase/",
}


# have to remap prefixes from prefixmaps in order to match the prefixes in Minerva
def remap_prefixes(cmap):
    """Remaps prefixes from prefixmaps in order to match the prefixes in Minerva."""
    cmap.update(REWIRING)
    return cmap


def get_converter(context: str = "go") -> curies.Converter:
    """Get a converter for the given context."""
    converter = load_converter(context)
    # hacky solution to: https://github.com/geneontology/go-site/issues/2000
    converter = rewire(converter, REWIRING)
    return converter


def get_prefixes(context: str = "go"):
    """Returns a dictionary of all prefixes in the GO namespace."""
    converter = get_converter(context)
    cmaps = converter.prefix_map
    return cmaps
