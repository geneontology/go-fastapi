"""Module contains the API endpoints for handling prefixes and expansions."""

import logging

from curies import Converter
from fastapi import APIRouter, Path, Query

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.prefix_utils import get_prefixes

logger = logging.getLogger()

router = APIRouter()


@router.get(
    "/api/identifier/prefixes",
    tags=["identifier/prefixes"],
    description="Returns a list of all prefixes in the GO namespace.",
)
async def get_all_prefixes():
    """Returns a list of all prefixes in the GO namespace."""
    all_prefixes = []
    for k, _v in get_prefixes("go").items():
        all_prefixes.append(k)
    return all_prefixes


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
    if ":" not in id:
        raise ValueError("Invalid CURIE format")

    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")

    cmaps = get_prefixes("go")
    # have to set strict to "False" to allow for WB and WormBase as prefixes that
    # map to the same expanded URI prefix
    converter = Converter.from_prefix_map(cmaps, strict=False)
    expanded = converter.expand(id)
    if not expanded:
        raise DataNotFoundException(detail=f"Item with ID {id} not found")
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
    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    compressed = converter.compress(uri)
    if not compressed:
        raise DataNotFoundException(detail=f"Item with URI {uri} not found")
    return converter.compress(uri)
