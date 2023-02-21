import logging
from pprint import pprint
from typing import List, Union

from fastapi import APIRouter, Query
from ontobio.golr.golr_query import GolrSearchQuery
from ontobio.util.user_agent import get_user_agent
from pydantic import BaseModel

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


def search(term, args):
    q = GolrSearchQuery(term, args)
    return q.search()


# @router.get("/api/search/entity/{term}", tags=["search"])
# async def search_term(term: str):
#     """
#     Returns list of matching concepts or entities using lexical search
#
#     :param term: search string, e.g. shh, cell
#
#     """
#     q = GolrSearchQuery(term, user_agent=USER_AGENT,
#                         url="http://golr-aux.geneontology.io/solr", )
#     results = q.search()
#     auto_result = {
#         "numFound": results.numFound,
#         "docs": results.docs,
#         "facet_counts": results.facet_counts,
#         "highlighting": results.highlighting
#     }
#     return auto_result


@router.get("/api/search/entity/autocomplete/{term}", tags=["search"])
async def autocomplete_term(
    term: str = Query(..., description="example: `biological`")
):
    """
    Returns list of matching concepts or entities using lexical search
    """
    q = GolrSearchQuery(
        term,
        user_agent=USER_AGENT,
        url="http://golr-aux.geneontology.io/solr",
    )
    results = q.autocomplete()
    docs = []
    for item in results.get("docs"):
        auto_result = {
            "id": item.id,
            "label": item.label,
            "match": item.match,
            "category": item.category,
            "taxon": item.taxon,
            "taxon_label": item.taxon_label,
            "highlight": item.highlight,
            "has_highlight": item.has_highlight,
        }
        docs.append(auto_result)
    result = {"docs": docs}
    return result
