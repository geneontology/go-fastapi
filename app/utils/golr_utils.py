"""golr utils."""

import requests

from app.exceptions.global_exceptions import DataNotFoundException
from app.routers.slimmer import gene_to_uniprot_from_mygene
from app.utils.settings import ESOLR, ESOLRDoc


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

    print(query)
    timeout_seconds = 60  # Set the desired timeout value in seconds

    try:
        response = requests.get(query, timeout=timeout_seconds)
        return response.json()["response"]["docs"][0]
        # Process the response here
    except IndexError:
        raise DataNotFoundException(detail=f"Item with ID {id} not found")
    except requests.Timeout as e:
        print(f"Request timed out: {e}")
    except requests.RequestException as e:
        print(f"No results found: {e}")


# (ESOLR.GOLR, ESOLRDoc.ANNOTATION, q, qf, fields, fq, False)
def gu_run_solr_text_on(
    solr_instance, category: str, q: str, qf: str, fields: str, optionals: str, highlight: bool = False
):
    """
    Return the result of a solr query on the given solrInstance, for a certain document_category and id.

    :param solr_instance: The solr instance to query
    :param category: The document category to query
    :param q: The query string
    :param qf: The query fields
    :param fields: The fields to return
    :param optionals: The optional parameters
    :param highlight: Whether to highlight the results
    :type highlight: bool
    :return: The result of the query

    """
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
    print(query)
    timeout_seconds = 60  # Set the desired timeout value in seconds

    try:
        response = requests.get(query, timeout=timeout_seconds)

        # solr returns matching text in the field "highlighting", but it is not included in the response.
        # We add it to the response here to make it easier to use. Highlighting is keyed by the id of the document
        if highlight:
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
        else:
            return_doc = []
            for doc in response.json()["response"]["docs"]:
                if doc.get("id") is not None and doc.get("id").startswith("MGI:"):
                    doc["id"] = doc["id"].replace("MGI:MGI:", "MGI:")
                return_doc.append(doc)
            return return_doc
            # Process the response here
    except requests.Timeout:
        print("Request timed out")
    except requests.RequestException as e:
        print(f"Request error: {e}")

def is_valid_bioentity(entity_id) -> bool:
    """
    Check if the provided identifier is valid by querying the AmiGO Solr (GOLR) instance.

    :param entity_id: The bioentity identifier
    :type entity_id: str
    :return: True if the entity identifier is valid, False otherwise.
    :rtype: bool
    """
    # Ensure the GO ID starts with the proper prefix
    if ":" not in entity_id:
        raise ValueError("Invalid CURIE format")

    if "MGI:" in entity_id:
        if "MGI:MGI:" in entity_id:
            pass
        else:
            entity_id = entity_id.replace("MGI:", "MGI:MGI:")

    fields = ""

    try:
        data = run_solr_on(ESOLR.GOLR, ESOLRDoc.BIOENTITY, entity_id, fields)
        if data:
            return True
    except DataNotFoundException as e:
        # Log the exception if needed
        fix_possible_hgnc_id = gene_to_uniprot_from_mygene(entity_id)
        print(fix_possible_hgnc_id)
        try:
            if fix_possible_hgnc_id:
                data = run_solr_on(ESOLR.GOLR, ESOLRDoc.BIOENTITY, fix_possible_hgnc_id[0], fields)
                if data:
                    return True
        except DataNotFoundException as e:
            print(f"Exception occurred: {e}")
            # Propagate the exception and return False
            raise e

    # Default return False if no data is found
    return False
