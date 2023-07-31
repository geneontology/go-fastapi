"""golr utils."""
import logging

import requests

logger = logging.getLogger(__name__)


# Respect the method name for run_sparql_on with enums
def run_solr_on(solr_instance, category, id, fields):
    """Return the result of a solr query on the given solrInstance, for a certain document_category and id."""
    query = (
        solr_instance.value
        + 'select?q=*:*&fq=document_category:"'
        + category.value
        + '"&fq=id:"'
        + id
        + '"&fl='
        + fields
        + "&wt=json&indent=on"
    )
    response = requests.get(query)
    return response.json()["response"]["docs"][0]


# (ESOLR.GOLR, ESOLRDoc.ANNOTATION, q, qf, fields, fq)
def run_solr_text_on(solr_instance, category, q, qf, fields, optionals):
    """Return the result of a solr query on the given solrInstance, for a certain document_category and id."""
    solr_url = solr_instance.value

    if optionals is None:
        optionals = ""
    query = (
        solr_url
        + "select?q="
        + q
        + "&qf="
        + qf
        + '&fq=document_category:"'
        + category.value
        + '"&fl='
        + fields
        + "&hl=on&hl.snippets=1000&hl.fl=bioentity_name_searchable,bioentity_label_searchable,bioentity_class,"
        + "annotation_class_label_searchable,&hl.requireFieldMatch=true"
        + "&wt=json&indent=on"
        + optionals
    )
    response = requests.get(query)

    # solr returns matching text in the field "highlighting", but it is not included in the response.
    # We add it to the response here to make it easier to use. Highlighting is keyed by the id of the document
    highlight_added = []
    for doc in response.json()["response"]["docs"]:
        if doc.get("id") is not None and doc.get("id") in response.json()["highlighting"]:
            doc["highlighting"] = response.json()["highlighting"][doc["id"]]
            if doc.get("id").startswith("MGI:"):
                doc["id"] = doc["id"].replace("MGI:MGI:", "MGI:")
        else:
            doc["highlighting"] = {}
        highlight_added.append(doc)
    return highlight_added
