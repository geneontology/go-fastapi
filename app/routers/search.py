import logging
from pprint import pprint

from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import GolrSearchQuery
log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()


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
