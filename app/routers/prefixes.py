import logging

from fastapi import APIRouter, Query
from prefixcommons.curie_util import contract_uri, expand_uri, get_prefixes, read_biocontext

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    cmaps = [read_biocontext('go_context')]
    return get_prefixes()


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(
    id: str = Query(
        None, description="identifier in CURIE format of the resource to expand"
    )
):
    cmaps = [read_biocontext('go_context')]
    return expand_uri(id=id, cmaps=cmaps)


@router.get("/api/identifier/prefixes/contract/", tags=["identifier/prefixes"])
async def get_contract_uri(
    url: str = Query(..., description="full URI of the identified resource")
):
    """
    Enter a full URI of the identified resource to contract to CURIE format
    e.g. http://purl.obolibrary.org/obo/GO_0008150
    """
    cmaps = [read_biocontext('go_context')]
    return contract_uri(url)
