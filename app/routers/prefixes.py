import logging
from fastapi import APIRouter, Query
from app.utils.prefixes.prefix_utils import get_prefixes
from pprint import pprint
from curies import Converter
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    all_prefixes = []
    for k, v in get_prefixes("go").items():
        all_prefixes.append(k)
    return all_prefixes


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(
    id: str = Query(
        None, description="identifier in CURIE format of the resource to expand"
    )
):
    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")

    cmaps = get_prefixes("go")
    # have to set strict to "False" to allow for WB and WormBase as prefixes that
    # map to the same expanded URI prefix
    converter = Converter.from_prefix_map(cmaps, strict=False)
    return converter.expand(id)


@router.get("/api/identifier/prefixes/contract/", tags=["identifier/prefixes"])
async def get_contract_uri(
    uri: str):
    """
    Enter a full URI of the identified resource to contract to CURIE format
    e.g. http://purl.obolibrary.org/obo/GO_0008150
    """
    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    return converter.compress(uri)
