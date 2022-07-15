import logging
from prefixcommons.curie_util import get_prefixes, expand_uri, contract_uri
from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    return get_prefixes()


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(id: str = Query(None, description="identifier in CURIE format of the resource to expand")):
    return expand_uri(id)


@router.get("/api/identifier/prefixes/contract/{uri}", tags=["identifier/prefixes"])
async def get_contract_uri(uri: str = Query(None, description="full URI of the identified resource")):
    print(uri)
    return contract_uri(uri)
