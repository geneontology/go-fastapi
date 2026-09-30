"""golr utils."""

import re
from typing import List, Optional
from urllib.parse import quote
from zipfile import error

import requests

from app.exceptions.global_exceptions import DataNotFoundException, InvalidIdentifier
from app.utils.mygene_utils import gene_to_uniprot_from_mygene
from app.utils.retry_utils import retry_on_golr_error
from app.utils.settings import ESOLR, ESOLRDoc, logger


def solr_encode_query_value(user_text: str) -> str:
    """
    Percent-encode caller text for concatenation into a GOlr query string.

    Without this an unencoded "&" starts a new Solr parameter rather than
    being searched for. "+" is left raw deliberately: it decodes to a space
    downstream, and encoding it would change what multi-word terms match.
    Expects raw input -- applying it twice escapes the first pass's percents.

    :param user_text: caller-supplied text
    :return: percent-encoded text safe to concatenate into a query string
    """
    return quote(user_text, safe="+")


# Identifier characters: enough for every CURIE GOlr stores (ECO:0000314,
# NCBITaxon:9606, ZFIN:ZDB-PUB-060503-2), none with meaning inside a quoted
# Solr phrase or a URL query string.
SOLR_FILTER_VALUE = re.compile(r"[A-Za-z0-9_.:-]+")


def validate_solr_filter_values(values: Optional[List[str]], param_name: str) -> Optional[List[str]]:
    """
    Reject filter values that could carry Solr or query-string syntax.

    Filter values are identifiers that end up inside a quoted phrase of an fq
    clause. A quote, backslash, space, parenthesis, ampersand or wildcard in one
    lets a caller close the phrase and write the rest of the query. Legitimate
    values never contain those characters, so this costs nothing.

    :param values: caller-supplied values, or None when the filter is absent
    :param param_name: the query parameter's name, for the error message
    :return: the values, unchanged
    :raises InvalidIdentifier: on the first value outside the identifier character set
    """
    if values is None:
        return None
    for value in values:
        if not SOLR_FILTER_VALUE.fullmatch(value):
            raise InvalidIdentifier(
                detail=f"Invalid {param_name} value {value!r}: expected an identifier "
                "(letters, digits, ':', '_', '.', '-')"
            )
    return values


def solr_phrase_filter(field: str, values: Optional[List[str]]) -> str:
    """
    Build an fq clause matching any of the values as exact phrases, or "" when there are none.

    Produces the shape the routers have always sent: &fq=<field>:("a","b").
    Caller-supplied values must have passed validate_solr_filter_values first.

    :param field: the Solr field to filter on
    :param values: identifiers to match, or None
    :return: the clause to append to the query string
    """
    if not values:
        return ""
    return "&fq=" + field + ":(" + ",".join('"' + value + '"' for value in values) + ")"


# Respect the method name for run_sparql_on with enums
@retry_on_golr_error(max_retries=3, delay=2)
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
        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from GOLr: {e}")
            raise ValueError(f"Invalid JSON response from GOLr server: {e}") from e
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
    )

    # Only add highlighting parameters if requested
    if highlight:
        query += ("&hl=on&hl.snippets=1000&hl.fl=bioentity_name_searchable,bioentity_label_searchable,bioentity_class,"
                  + "annotation_class_label_searchable,&hl.requireFieldMatch=true")

    query += "&wt=json&indent=on" + optionals
    logger.info(query)
    timeout_seconds = 60  # Set the desired timeout value in seconds

    try:
        response = requests.get(query, timeout=timeout_seconds)
        response.raise_for_status()  # Raise an error for non-2xx responses
        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from GOLr: {e}")
            raise ValueError(f"Invalid JSON response from GOLr server: {e}") from e

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


@retry_on_golr_error(max_retries=3, delay=2)
def get_bioentity_isoforms(entity_id: str) -> list[str]:
    """
    Query GOlr annotations to retrieve all isoform IDs associated with a canonical bioentity.

    The bioentity document type in GOlr does not carry isoform information.
    However, annotation documents have a `bioentity_isoform` field that records
    the specific isoform used in each annotation. A facet query on this field
    (with rows=0) efficiently returns the distinct isoform IDs without
    transferring full annotation documents.

    This is needed because GO-CAM models may reference isoform-specific IDs
    (e.g. UniProtKB:P08887-2) rather than the canonical ID (UniProtKB:P08887).
    See: https://github.com/geneontology/go-fastapi/issues/135

    :param entity_id: A canonical bioentity CURIE (e.g. "UniProtKB:P08887")
    :return: List of isoform CURIEs (may include the canonical ID itself)
    """
    query = (
        ESOLR.GOLR.value
        + 'select?q=*:*&fq=document_category:"'
        + ESOLRDoc.ANNOTATION.value
        + '"&fq=bioentity:"'
        + entity_id
        + '"&rows=0&facet=true&facet.field=bioentity_isoform&facet.mincount=1&facet.limit=-1&wt=json'
    )

    timeout_seconds = 60
    response = requests.get(query, timeout=timeout_seconds)
    response.raise_for_status()
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from GOLr: {e}")
        raise ValueError(f"Invalid JSON response from GOLr server: {e}") from e
    # Facet field response is alternating [value, count, value, count, ...]
    facet_list = (
        data.get("facet_counts", {})
        .get("facet_fields", {})
        .get("bioentity_isoform", [])
    )
    return [facet_list[i] for i in range(0, len(facet_list), 2) if facet_list[i]]


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
