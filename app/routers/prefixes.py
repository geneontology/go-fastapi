import logging
from fastapi import APIRouter, Query
from prefixcommons.curie_util import contract_uri, expand_uri, get_prefixes, read_biocontext

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    cmaps = [read_biocontext("go_context")]
    for d in cmaps:
        d.update((k, "http://identifiers.org/mgi/MGI:") for k, v in d.items() if v == "http://identifiers.org/mgi/")
    return get_prefixes(cmaps)


@router.get("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_expand_curie(
    id: str = Query(
        None, description="identifier in CURIE format of the resource to expand"
    )
):
    cmaps = [read_biocontext("go_context")]
    for d in cmaps:
        d.update((k, "http://identifiers.org/mgi/MGI:") for k, v in d.items() if v == "http://identifiers.org/mgi/")
    return expand_uri(id=id, cmaps=cmaps)


@router.get("/api/identifier/prefixes/contract/", tags=["identifier/prefixes"])
async def get_contract_uri(
    uri: str):
    """
    Enter a full URI of the identified resource to contract to CURIE format
    e.g. http://purl.obolibrary.org/obo/GO_0008150
    """
    return contract_uri(uri)
