import logging
from fastapi import APIRouter
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import GolrSearchQuery

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()

def search(term, args):
    q = GolrSearchQuery(term, args)
    return q.search()


@router.post("/api/search/entity/{term}", tags=["search"])
async def search_term(term: str,
                      category: str,
                      boost_fix: str,
                      boost_q: str,
                      taxon: str,
                      highlight_class: str,
                      rows: int = 20,
                      start: int = 0):
    # TODO @api.marshal_with(search_result)
    """
    Returns list of matching concepts or entities using lexical search

    :param term: search string, e.g. shh, cell
    :param category: e.g. gene, disease
    :param boost_fix: boost function e.g. pow(edges,0.334)
    :param boost_q: boost query e.g. category:genotype^-10
    :param taxon: taxon filter, eg NCBITaxon:9606, includes inferred taxa
    :param highlight_class: highlight class
    :param rows: number of rows
    :param start: number to start from

    """
    q = GolrSearchQuery(term, user_agent=USER_AGENT)
    results = q.search()
    return results
