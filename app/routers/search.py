import logging
from enum import Enum

from fastapi import APIRouter, Query

from app.utils.golr.golr_utils import run_solr_text_on
from app.utils.settings import ESOLR, ESOLRDoc, get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()

class AutocompleteCategory(str, Enum):
    """
    The category of items to retrieve, can be 'gene' or 'term'
    """
    gene = "gene"
    term = "term"


@router.get("/api/search/entity/autocomplete/{term}", tags=["search"])
async def autocomplete_term(
    term: str = Query(..., description="example: `biological`"),
    start: int = 0,
    rows: int = 100,
    category: AutocompleteCategory = Query(
        None,
        description="The category of items to retrieve, can " "be 'gene' or 'term'",
    ),
):
    """
    Returns a list of matching concepts or entities over annotation classes (e.g. GO terms) and
    bioentities (e.g. gene names and symbols).

    :param term: The search term for autocomplete.
    :type term: str
    :param start: The starting index of the search results, defaults to 0.
    :type start: int, optional
    :param rows: The maximum number of rows to return in the search results, defaults to 100.
    :type rows: int, optional
    :param category: The category of items to retrieve, can be 'gene' or 'term', defaults to None.
    :type category: AutocompleteCategory, optional

    :return: A dictionary containing the list of matching concepts or entities.
    :rtype: dict
    """
    # dictates the fields to return
    fields = "id,bioentity_label,bioentity_name,taxon,taxon_label,document_category"

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

    if category == "gene":
        category = ESOLRDoc.BIOENTITY
    else:
        category = ESOLRDoc.ANNOTATION

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows)
    data = run_solr_text_on(ESOLR.GOLR, category, term + "*", query_fields, fields, optionals)
    docs = []

    for item in data:
        if category == "term":
            label = item.get("annotation_class_label")
            name = item.get("annotation_class")
        else:
            label = item.get("bioentity_label")
            name = item.get("bioentity_name")
        auto_result = {
            "id": item.get("id"),
            "label": label,
            "category": item.get("category"),
            "taxon": item.get("taxon"),
            "taxon_label": item.get("taxon_label"),
            "name": name,
            "highlight": item.get("highlighting"),
            "match": item.get("highlighting"),
            "has_highlight": True if item.get("highlighting") else False,
        }
        docs.append(auto_result)

    result = {"docs": docs}
    return result
