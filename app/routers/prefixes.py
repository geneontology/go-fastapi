import logging
from prefixcommons.curie_util import get_prefixes, expand_uri, contract_uri
from fastapi import APIRouter
from ontobio.util.user_agent import get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


@router.post("/api/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
        """
        Returns list of prefixes
        """
        return get_prefixes()


@router.post("/api/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def expand_curie(id: str):
        """
        Returns expanded URI
        id: ID of entity to be contracted to URI, e.g "MGI:1"
        """
        return expand_uri(id)


@router.post("/api/identifier/prefixes/contract/{uri}", tags=["identifier/prefixes"])
async def contract_uri(uri: str):
        """
        Returns contracted URI
        uri: URI of entity to be contracted to identifier/CURIE, e.g "http://www.informatics.jax.org/accession/MGI:1"
        """
        return contract_uri(uri)
    

    
    

