import logging
from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent
from pprint import pprint
from app.utils.golr.golr_utls import run_solr_text_on
from app.utils.settings import ESOLR, ESOLRDoc

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()


@router.get("/api/search/entity/autocomplete/{term}", tags=["search"])
async def autocomplete_term(
    term: str = Query(..., description="example: `biological`"),
    start: int = 0,
    rows: int = 100,
    category: str = Query(None, description="example: `gene`"),
):
    """
    Returns list of matching concepts or entities using lexical search
    """

    # dictates the fields to return, annotation_class,aspect
    fields = (
        "id,bioentity_label,bioentity_name,taxon,taxon_label,category"
    )

    # TODO: figure out category
    # boost fields %5E2 -> ^2, %5E1 -> ^1
    query_filters = (
        "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf="
        "bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf="
        "annotation_extension_class%5E2&qf=annotation_extension_class_label_searchable%5E1&qf="
        "reference_searchable%5E1&qf=panther_family_searchable%5E1&qf="
        "panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"
    )

    # if category != 'gene' and category != 'term':
    #     raise NotImplementedError("category must be 'gene' or 'term'")

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows)
    data = run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.BIOENTITY, term, query_filters, fields, optionals
    )
    docs = []

    for item in data:
        auto_result = {
            "id": item.get('id'),
            "label": item.get('bioentity_label'),
            "category": item.get('category'),
            "taxon": item.get('taxon'),
            "taxon_label": item.get('taxon_label'),
        }
        docs.append(auto_result)
    result = {"docs": docs}
    pprint(result)
    return result
