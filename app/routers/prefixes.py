"""Module contains the API endpoints for handling prefixes and expansions."""
import logging

from curies import Converter
from fastapi import APIRouter, Path, Query

from app.utils.prefix_utils import get_prefixes

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    """Returns a list of all prefixes in the GO namespace."""
    all_prefixes = []
    for k, _v in get_prefixes("go").items():
        all_prefixes.append(k)
    return all_prefixes


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(id: str = Path(..., description="identifier in CURIE format of the resource to expand")):
    """
    Enter a CURIE of the identified resource to expand to full URI format.

    e.g. MGI:3588192, MGI:MGI:3588192, ZFIN:ZDB-GENE-000403-1.
    """
    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")

    cmaps = get_prefixes("go")
    # have to set strict to "False" to allow for WB and WormBase as prefixes that
    # map to the same expanded URI prefix
    converter = Converter.from_prefix_map(cmaps, strict=False)
    return converter.expand(id)


@router.get("/api/identifier/prefixes/contract/", tags=["identifier/prefixes"])
async def get_contract_uri(uri: str = Query(None, description="URI of the resource to contract")):
    """
    Enter a full URI of the identified resource to contract to CURIE format.

    e.g. http://purl.obolibrary.org/obo/GO_0008150.
    """
    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    return converter.compress(uri)
