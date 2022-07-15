import logging
from typing import List, Union
from pprint import pprint
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import GolrSearchQuery
from fastapi import APIRouter, Query
from pydantic import BaseModel

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


def search(term, args):
    q = GolrSearchQuery(term, args)
    return q.search()


class TestResult(BaseModel):
    id: Union[str, None] = None
    label: List[str] = []
    match: Union[str, None] = None
    category: List[str] = []
    taxon: Union[str, None] = None
    taxon_label: Union[str, None] = None
    highlight: Union[str, None] = None
    has_highlight: Union[str, None] = None


@router.get("/api/search/entity/{term}", tags=["search"])
async def search_term(term: str):
    """
    Returns list of matching concepts or entities using lexical search

    :param term: search string, e.g. shh, cell

    """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.search()
    return results


@router.get('/api/search/entity/autocomplete/{term}', tags=["search"], response_model=TestResult)
async def autocomplete_term(term: str = Query(..., description="example: `biological`")):
    """
        Returns list of matching concepts or entities using lexical search
        """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.autocomplete()
    pprint(results)
    return results
