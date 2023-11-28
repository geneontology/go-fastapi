"""Module contains the API endpoints for handling prefixes and expansions."""
import logging

from fastapi import APIRouter, Path, Query

from app.utils.prefix_utils import get_converter

logger = logging.getLogger()

router = APIRouter()
converter = get_converter("go")


@router.get(
    "/api/identifier/prefixes",
    tags=["identifier/prefixes"],
    description="Returns a list of all prefixes in the GO namespace.",
)
async def get_all_prefixes():
    """Returns a list of all prefixes in the GO namespace."""
    return list(converter.prefix_map)


@router.get(
    "/api/identifier/prefixes/expand/{id}",
    tags=["identifier/prefixes"],
    description="Enter a CURIE of the identified resource to expand to full URI format.  "
    "e.g. MGI:3588192, MGI:MGI:3588192",
)
async def get_expand_curie(id: str = Path(..., description="identifier in CURIE format of the resource to expand")):
    """
    Enter a CURIE of the identified resource to expand to full URI format.

    e.g. MGI:3588192, MGI:MGI:3588192, ZFIN:ZDB-GENE-000403-1.
    """
    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")
    return converter.expand(id)


@router.get(
    "/api/identifier/prefixes/contract/",
    tags=["identifier/prefixes"],
    description="Enter a full URI of the identified resource to contract to CURIE format, "
    "e.g. 'http://purl.obolibrary.org/obo/GO_0008150'.",
)
async def get_contract_uri(uri: str = Query(..., description="URI of the resource to contract")):
    """
    Enter a full URI of the identified resource to contract to CURIE format.

    e.g. http://purl.obolibrary.org/obo/GO_0008150.
    """
    return converter.compress(uri)
