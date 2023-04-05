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

    # dictates the fields to return
    fields = (
        "id,bioentity_label,bioentity_name,taxon,taxon_label,document_category"
    )

    # TODO: figure out category
    # In Solr, the qf (Query Fields) parameter is used to specify which fields in the
    # index should be searched when executing a query.
    # annotation_class == term, annotation_class_label == term label
    # boost fields %5E2 -> ^2, %5E1 -> ^1
    query_fields = (
        "bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf="
        "annotation_class_label_searchable%5E1&qf="
        "annotation_extension_class_label_searchable%5E1&qf="
        "panther_family_searchable%5E1&qf=panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"
    )

    if category == 'gene':
        category = ESOLRDoc.BIOENTITY
    else:
        category = ESOLRDoc.ANNOTATION

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows)
    data = run_solr_text_on(
        ESOLR.GOLR, category, term+"*", query_fields, fields, optionals
    )
    docs = []

    for item in data:
        if category == 'term':
            label = item.get('annotation_class_label')
            name = item.get('annotation_class')
        else:
            label = item.get('bioentity_label')
            name = item.get('bioentity_name')
        auto_result = {
            "id": item.get('id'),
            "label": label,
            "category": item.get('category'),
            "taxon": item.get('taxon'),
            "taxon_label": item.get('taxon_label'),
            "name": name
        }
        docs.append(auto_result)

    result = {"docs": docs}
    pprint(result)
    return result
