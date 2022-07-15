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


class AResult(BaseModel):
    id: Union[str, None] = None
    label: List[str] = []
    match: Union[str, None] = None
    category: List[str] = []
    taxon: Union[str, None] = None
    taxon_label: Union[str, None] = None
    highlight: Union[str, None] = None
    has_highlight: Union[str, None] = None


class TestResult(BaseModel):
    docs: List[AResult] = []

# {docs: [AutocompleteResult]}

@router.get("/api/search/entity/{term}", tags=["search"])
async def search_term(term: str):
    """
    Returns list of matching concepts or entities using lexical search

    :param term: search string, e.g. shh, cell

    """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.search()
    return results


@router.get('/api/search/entity/autocomplete/{term}', tags=["search"])
async def autocomplete_term(term: str = Query(..., description="example: `biological`")):
    """
        Returns list of matching concepts or entities using lexical search
        """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.autocomplete()
    docs = []
    for item in results.get('docs'):
        auto_result = {"id": item.id,
                       "label": item.label,
                       "match": item.match,
                       "category": item.category,
                       "taxon": item.taxon,
                       "taxon_label": item.taxon_label,
                       "highlight": item.highlight,
                       "has_highlight": item.has_highlight}
        docs.append(auto_result)
    return results
