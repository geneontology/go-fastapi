import logging
from typing import List, Union
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


class AutocompleteResult(BaseModel):
    id: str
    label: List[str]
    match: str
    category: List[str]
    taxon: str
    taxon_label: str
    highlight: str
    has_highlight: str



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
    return results

 #
 # {
 #      "id": "NCBIGene:49413",
 #      "label": [
 #        "Go"
 #      ],
 #      "match": "Go",
 #      "category": [
 #        "gene",
 #        "sequence feature"
 #      ],
 #      "taxon": "NCBITaxon:7227",
 #      "taxon_label": "Drosophila melanogaster",
 #      "highlight": "<em class=\"hilite\">Go</em>",
 #      "has_highlight": true
 #    },