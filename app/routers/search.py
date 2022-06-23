import logging
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import GolrSearchQuery
from fastapi import APIRouter, Query

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


def search(term, args):
    q = GolrSearchQuery(term, args)
    return q.search()


@router.get("/search/entity/{term}", tags=["search"])
async def search_term(term: str):
    # TODO @api.marshal_with(search_result)
    """
    Returns list of matching concepts or entities using lexical search

    :param term: search string, e.g. shh, cell

    """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.search()
    return results


@router.get('/search/entity/autocomplete/{term}', tags=["search"])
async def autocomplete_term(term: str = Query(..., description="example: `biological`")):
    """
        Returns list of matching concepts or entities using lexical search
        """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.autocomplete()
    return results
