import logging
from fastapi import APIRouter, Query
from prefixmaps import load_context
from curies import Converter
from app.utils.prefixes.prefix_utils import remap_prefixes
from prefixcommons.curie_util import contract_uri, expand_uri, get_prefixes
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    context = load_context("go")
    extended_prefix_map = context.as_extended_prefix_map()
    converter = Converter.from_extended_prefix_map(extended_prefix_map)
    cmaps = converter.prefix_map
    # hacky solution to: https://github.com/geneontology/go-site/issues/2000
    cmaps = remap_prefixes(cmaps)
    return get_prefixes(cmaps)


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(
    id: str = Query(
        None, description="identifier in CURIE format of the resource to expand"
    )
):
    context = load_context("go")
    extended_prefix_map = context.as_extended_prefix_map()
    converter = Converter.from_extended_prefix_map(extended_prefix_map)
    cmaps = converter.prefix_map
    # hacky solution to: https://github.com/geneontology/go-site/issues/2000
    cmaps = remap_prefixes(cmaps)
    return expand_uri(id=id, cmaps=cmaps)


@router.get("/api/identifier/prefixes/contract/", tags=["identifier/prefixes"])
async def get_contract_uri(
    uri: str):
    """
    Enter a full URI of the identified resource to contract to CURIE format
    e.g. http://purl.obolibrary.org/obo/GO_0008150
    """
    return contract_uri(uri)
