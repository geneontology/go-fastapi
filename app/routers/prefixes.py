import logging

from fastapi import APIRouter, Query
from prefixcommons.curie_util import contract_uri, expand_uri, get_prefixes

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    return get_prefixes()


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(
    id: str = Query(
        None, description="identifier in CURIE format of the resource to expand"
    )
):
    return expand_uri(id)


@router.get("/api/identifier/prefixes/contract/{uri}", tags=["identifier/prefixes"])
async def get_contract_uri(
    uri: str = Query(None, description="full URI of the identified resource")
):
    logger.info(uri)
    return contract_uri(uri)
