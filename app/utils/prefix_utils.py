"""prefix utility functions."""
import logging

from curies import Converter
from prefixmaps import load_converter

logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


# have to remap prefixes from prefixmaps in order to match the prefixes in Minerva
def remap_prefixes(cmap):
    """Remaps prefixes from prefixmaps in order to match the prefixes in Minerva."""
    cmap["MGI"] = "http://identifiers.org/mgi/MGI:"
    cmap["WB"] = "http://identifiers.org/wormbase/"
    return cmap


def get_prefixes(context: str = "go"):
    """Returns a dictionary of all prefixes in the GO namespace."""
    converter = load_converter(context)
    cmaps = converter.prefix_map
    # hacky solution to: https://github.com/geneontology/go-site/issues/2000
    # TODO consider using curies' rewiring functionality
    #  https://curies.readthedocs.io/en/latest/reconciliation.html#rewiring
    cmap_remapped = remap_prefixes(cmaps)

    return cmap_remapped
