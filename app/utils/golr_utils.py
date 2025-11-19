"""golr utils."""

from zipfile import error

import requests

from app.exceptions.global_exceptions import DataNotFoundException
from app.routers.slimmer import gene_to_uniprot_from_mygene
from app.utils.rate_limiter import rate_limit_golr, retry_on_golr_error
from app.utils.settings import ESOLR, ESOLRDoc, logger


# Respect the method name for run_sparql_on with enums
@retry_on_golr_error(max_retries=3, delay=2)
@rate_limit_golr
def run_solr_on(solr_instance, category, id, fields):
    """Return the result of a Solr query."""
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

    logger.info(f"Solr query: {query}")
    timeout_seconds = 60

    try:
        response = requests.get(query, timeout=timeout_seconds)
        response.raise_for_status()  # Raise an error for non-2xx responses
        response_json = response.json()
        logger.info("Solr response JSON:", response_json)

        docs = response_json.get("response", {}).get("docs", [])
        if not docs:
            raise DataNotFoundException(detail=f"Item with ID {id} not found")
        return docs[0]

    except IndexError as e:
        logger.info("IndexError: No docs found, raising DataNotFoundException")
        raise DataNotFoundException(detail=f"Item with ID {id} not found") from e
    except requests.Timeout as e:
        logger.info(f"Request timed out: {e}")
        raise
    except requests.RequestException as e:
        logger.info(f"Request failed: {e}")
        raise


# (ESOLR.GOLR, ESOLRDoc.ANNOTATION, q, qf, fields, fq, False)
@retry_on_golr_error(max_retries=3, delay=2)
@rate_limit_golr
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
    logger.info(query)
    timeout_seconds = 60  # Set the desired timeout value in seconds

    try:
        response = requests.get(query, timeout=timeout_seconds)
        response.raise_for_status()  # Raise an error for non-2xx responses
        response_json = response.json()

        # solr returns matching text in the field "highlighting", but it is not included in the response.
        # We add it to the response here to make it easier to use. Highlighting is keyed by the id of the document
        if highlight:
            highlight_added = []
            for doc in response_json["response"]["docs"]:
                if doc.get("id") is not None and doc.get("id") in response_json["highlighting"]:
                    doc["highlighting"] = response_json["highlighting"][doc["id"]]
                    if doc.get("id").startswith("MGI:"):
                        doc["id"] = doc["id"].replace("MGI:MGI:", "MGI:")
                else:
                    doc["highlighting"] = {}
                highlight_added.append(doc)
            return highlight_added
        else:
            return_doc = []
            for doc in response_json["response"]["docs"]:
                if doc.get("id") is not None and doc.get("id").startswith("MGI:"):
                    doc["id"] = doc["id"].replace("MGI:MGI:", "MGI:")
                return_doc.append(doc)
            return return_doc
            # Process the response here
    except requests.Timeout as e:
        logger.error(f"Request timed out: {e}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        raise


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
    except DataNotFoundException:
        if "HGNC" in entity_id:
            try:
                fix_possible_hgnc_id = gene_to_uniprot_from_mygene(entity_id)
            except DataNotFoundException as e:
                logger.info(f"Data Not Found Exception occurred: {e}")
                # Propagate the exception and return False
                raise e from error
            try:
                if fix_possible_hgnc_id:
                    data = run_solr_on(ESOLR.GOLR, ESOLRDoc.BIOENTITY, fix_possible_hgnc_id[0], fields)
                    if data:
                        return True
            except DataNotFoundException as e:
                logger.info(f"Data Not Found Exception occurred: {e}")
                logger.info("No results found for the provided entity ID")
                # Propagate the exception and return False
                raise e from error
        else:
            raise DataNotFoundException(detail=f"Bioentity with ID {entity_id} not found") from error
    except Exception as e:
        logger.info(f"Unexpected error in gene_to_uniprot_from_mygene: {e}")
        return False
    return False
