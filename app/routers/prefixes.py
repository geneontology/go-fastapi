import logging
from prefixcommons.curie_util import get_prefixes, expand_uri, contract_uri
from fastapi import APIRouter
from ontobio.util.user_agent import get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


@router.get("/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
    """
        :return: all prefixes
        """
    return get_prefixes()


@router.get("/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def expand_curie(id: str):
    """

        :param id: ID in CURIE form to expand
        :return: expanded IRI (full URL to resorce being expanded)
        """
    return expand_uri(id)


@router.get("/identifier/prefixes/contract/{uri}", tags=["identifier/prefixes"])
async def contract_uri(uri: str):
    """

        :param uri: expanded IRI (full URL to resorce being expanded)
        :return: CURIE 
        """
    return contract_uri(uri)
