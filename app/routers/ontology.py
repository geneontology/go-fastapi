"""Ontology-related endpoints."""

import json
import logging
from enum import Enum
from typing import List

from curies import Converter
from fastapi import APIRouter, Path, Query
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from pydantic import BaseModel

import app.utils.ontology_utils as ontology_utils
from app.exceptions.global_exceptions import DataNotFoundException, InvalidIdentifier
from app.utils.golr_utils import gu_run_solr_text_on, run_solr_on
from app.utils.prefix_utils import get_prefixes
from app.utils.settings import ESOLR, ESOLRDoc, get_sparql_endpoint, get_user_agent
from app.utils.sparql_utils import transform, transform_array

logger = logging.getLogger()


USER_AGENT = get_user_agent()
router = APIRouter()


class GraphType(str, Enum):

    """Enum for the different types of graphs that can be returned."""

    topology_graph = "topology_graph"


@router.get("/api/ontology/term/{id}", tags=["ontology"])
async def get_term_metadata_by_id(
    id: str = Path(
        ..., description="The ID of the term to extract the metadata from, e.g. GO:0003677", example="GO:0003677"
    ),
):
    """Returns metadata of an ontology term, e.g. GO:0003677."""
    try:
        ontology_utils.is_golr_recognized_curie(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    fields = "id,annotation_class_label,description,synonym,alternate_id,definition_xref,subset"
    doc = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, fields)

    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    goid_iri = converter.expand(id)

    result = {
        "goid": goid_iri,
        "label": doc.get("annotation_class_label", ""),
        "definition": doc.get("description", ""),
        "synonyms": doc.get("synonym", []),
        "relatedSynonyms": [],
        "alternativeIds": doc.get("alternate_id", []),
        "xrefs": doc.get("definition_xref", []),
        "subsets": doc.get("subset", []),
        "comment": "",
        "creation_date": ""
    }

    result["goid"] = converter.compress(result["goid"])
    return result


@router.get("/api/ontology/term/{id}/graph", tags=["ontology"])
async def get_term_graph_by_id(
    id: str = Path(
        ..., description="The ID of the term to extract the graph from,  e.g. GO:0003677", example="GO:0003677"
    ),
    graph_type: GraphType = Query(GraphType.topology_graph),
):
    """Returns graph of an ontology term, e.g. GO:0003677."""
    try:
        ontology_utils.is_valid_goid(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    graph_type = graph_type + "_json"  # GOLR field names

    data = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, graph_type)
    # step required as these graphs are made into strings in the json
    data[graph_type] = json.loads(data[graph_type])
    return data


@router.get(
    "/api/ontology/term/{id}/subgraph",
    tags=["ontology"],
    description="Extract a subgraph from an ontology term. e.g. GO:0003677 using the relationships is_a and part_of.",
)
async def get_subgraph_by_term_id(
    id: str = Path(
        ..., description="The ID of the term to extract the subgraph from,  e.g. GO:0003677", example="GO:0003677"
    ),
    start: int = Query(0, description="The start index of the results to return"),
    rows: int = Query(100, description="The number of results to return"),
):
    """
    Extract a subgraph from an ontology term. e.g. GO:0003677 using the relationships "is_a" and "part_of".

    :param id: The ID of the term to extract the subgraph from,  e.g. GO:0003677
    :param start: The start index of the results to return
    :param rows: The number of results to return
    :return: A is_a/part_of subgraph of the ontology term including the term's ancestors and descendants, label and ID.
    """
    try:
        ontology_utils.is_valid_goid(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    if rows is None:
        rows = 100000
    query_filters = ""
    golr_field_to_search = "isa_partof_closure"
    where_statement = "*:*&fq=" + golr_field_to_search + ":" + '"' + id + '"'
    fields = "id,annotation_class_label,isa_partof_closure,isa_partof_closure_label"
    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows)
    descendent_data = gu_run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.ONTOLOGY, where_statement, query_filters, fields, optionals, False
    )

    descendents = []
    for child in descendent_data:
        if child["id"] == id:
            pass
        else:
            child = {"id": child["id"]}
            descendents.append(child)

    golr_field_to_search = "id"
    where_statement = "*:*&fq=" + golr_field_to_search + ":" + '"' + id + '"'
    ancestor_data = gu_run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.ONTOLOGY, where_statement, query_filters, fields, optionals, False
    )
    ancestors = []
    for parent in ancestor_data[0]["isa_partof_closure"]:
        ancestors.append({"id": parent})

    data = {"descendents": descendents, "ancestors": ancestors}
    return data


@router.get(
    "/api/ontology/shared/{subject}/{object}",
    tags=["ontology"],
    description="Returns the ancestor ontology terms shared by two ontology terms. ",
)
async def get_ancestors_shared_by_two_terms(
    subject: str = Path(..., description="Identifier of a GO term, e.g. GO:0006259", example="GO:0006259"),
    object: str = Path(..., description="Identifier of a GO term, e.g. GO:0016070", example="GO:0016070"),
):
    """
    Returns the ancestor ontology terms shared by two ontology terms.

    :param subject: 'CURIE identifier of a GO term, e.g. GO:0006259'
    :param object: 'CURIE identifier of a GO term, e.g. GO:0016070'
    """
    try:
        ontology_utils.is_valid_goid(subject)
        ontology_utils.is_valid_goid(object)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    fields = "isa_partof_closure,isa_partof_closure_label"

    subres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, subject, fields)
    objres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, object, fields)

    logger.info("SUBJECT: ", subres)
    logger.info("OBJECT: ", objres)

    shared = []
    shared_labels = []
    for i in range(0, len(subres["isa_partof_closure"])):
        sub = subres["isa_partof_closure"][i]
        found = False
        if sub in objres["isa_partof_closure"]:
            found = True
        if found:
            shared.append(sub)
            shared_labels.append(subres["isa_partof_closure_label"][i])
    return {"goids": shared, "gonames: ": shared_labels}


@router.get(
    "/api/association/between/{subject}/{object}",
    tags=["ontology"],
    description="Returns the ancestor ontology terms shared by two ontology terms. ",
)
async def get_ancestors_shared_between_two_terms(
    subject: str = Path(..., description="Identifier of a GO term, e.g. GO:0006259", example="GO:0006259"),
    object: str = Path(..., description="Identifier of a GO term, e.g. GO:0016070", example="GO:0016070"),
    relation: str = Query(None, description="relation between two terms", example="closest"),
):
    """
    Returns the ancestor ontology terms shared by two ontology terms.

    :param subject: 'CURIE identifier of a GO term, e.g. GO:0006259'
    :param object: 'CURIE identifier of a GO term, e.g. GO:0016070'
    :param relation: 'relation between two terms' can only be one of two values: shared or closest
    """
    try:
        ontology_utils.is_valid_goid(subject)
        ontology_utils.is_valid_goid(object)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    fields = "isa_partof_closure,isa_partof_closure_label"
    logger.info(relation)
    if relation == "shared" or relation is None:
        subres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, subject, fields)
        objres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, object, fields)

        logger.info("SUBJECT: ", subres)
        logger.info("OBJECT: ", objres)

        shared = []
        shared_labels = []

        for i in range(0, len(subres["isa_partof_closure"])):
            sub = subres["isa_partof_closure"][i]
            found = False
            if sub in objres["isa_partof_closure"]:
                found = True
            if found:
                shared.append(sub)
                shared_labels.append(subres["isa_partof_closure_label"][i])

        result = {"shared": shared, "shared_labels": shared_labels}
        return result

    else:
        logger.info("got here")
        fields = "neighborhood_graph_json"
        # https://golr.geneontology.org/solr/select?q=*:*&fq=document_category:%22ontology_class%22&fq=id:%22GO:0006259%22&fl=neighborhood_graph_json&wt=json&indent=on
        subres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, subject, fields)
        objres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, object, fields)

        logger.info("SUBJECT: ", subres)
        logger.info("OBJECT: ", objres)
        data = json.loads(subres["neighborhood_graph_json"])
        data2 = json.loads(objres["neighborhood_graph_json"])

        is_a_set = set()
        part_of_set = set()
        for edge in data["edges"]:
            if edge.get("sub") == subject:
                if edge.get("pred") == "is_a":
                    is_a_set.add(edge.get("obj"))
                elif edge.get("pred") == "BFO:0000050":
                    part_of_set.add(edge.get("obj"))
            elif edge.get("obj") == subject:
                if edge.get("pred") == "is_a":
                    is_a_set.add(edge.get("sub"))
                elif edge.get("pred") == "BFO:0000050":
                    part_of_set.add(edge.get("sub"))

        is_a_set2 = set()
        part_of_set2 = set()

        for edge in data2["edges"]:
            if edge.get("sub") == object:
                if edge.get("pred") == "is_a":
                    is_a_set2.add(edge.get("obj"))
                elif edge.get("pred") == "BFO:0000050":
                    part_of_set2.add(edge.get("obj"))
            elif edge.get("obj") == object:
                if edge.get("pred") == "is_a":
                    is_a_set2.add(edge.get("sub"))
                elif edge.get("pred") == "BFO:0000050":
                    part_of_set2.add(edge.get("sub"))

        shared_is_a = []
        for isa in is_a_set:
            if isa in is_a_set2:
                shared_is_a.append(isa)

        shared_part_of = []
        combined_set = part_of_set | part_of_set2
        for part_of in combined_set:
            if part_of in part_of_set2:
                shared_part_of.append(part_of)

        result = {"sharedIsA": shared_is_a, "sharedPartOf": shared_part_of}
        return result


@router.get(
    "/api/go/{id}",
    tags=["ontology"],
    description="Returns GO term metadata (label, definition, synonyms, etc.) for a given GO term ID, e.g. GO:0008150",
)
async def get_go_term_detail_by_go_id(
    id: str = Path(..., description="A GO-Term CURIE (e.g. GO:0005885, GO:0097136)", example="GO:0008150")
):
    """
    Returns GO term metadata including label, definition, synonyms, alternative IDs, xrefs, and subsets.

    :param id: A GO-Term CURIE (e.g. GO:0008150)
    :return: GO term metadata including goid, label, definition, synonyms, alternativeIds, xrefs, subsets
    
    Note: This endpoint was migrated from the GO-CAM service API and may not be
    supported in its current form in the future.
    """
    try:
        ontology_utils.is_valid_goid(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    fields = "id,annotation_class_label,description,synonym,alternate_id,definition_xref,subset"
    doc = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, fields)

    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    goid_iri = converter.expand(id)

    result = {
        "goid": goid_iri,
        "label": doc.get("annotation_class_label", ""),
        "definition": doc.get("description", ""),
        "synonyms": doc.get("synonym", []),
        "relatedSynonyms": [],
        "alternativeIds": doc.get("alternate_id", []),
        "xrefs": doc.get("definition_xref", []),
        "subsets": doc.get("subset", []),
        "comment": "",
        "creation_date": ""
    }

    return result


class GOHierarchyItem(BaseModel):

    """
    A GO Hierarchy return model.

    This helps the hierarchy endpoint render in the swagger interface correctly,
    even when a return is missing a component here.

    :param GO: The GO ID.
    :param label: The label of the GO ID.
    :param hierarchy: The hierarchy of the GO ID.
    """

    GO: str
    label: str
    hierarchy: str


@router.get(
    "/api/go/{id}/hierarchy",
    tags=["ontology"],
    description="Returns parent and children relationships for a given GO ID, e.g. GO:0005885",
    response_model=List[GOHierarchyItem],
)
async def get_go_hierarchy_go_id(
    id: str = Path(..., description="A GO-Term ID, e.g. GO:0097136", example="GO:0008150")
):
    """
    Returns parent and children relationships for a given GO ID.

    e.g. GO:0005885
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    try:
        ontology_utils.is_valid_goid(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)

    collated_results = []

    fields = "id,annotation_class_label,isa_partof_closure,isa_partof_closure_label"
    doc = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, fields)

    query_term_iri = converter.expand(id)

    for i, (parent_id, parent_label) in enumerate(
        zip(doc.get("isa_partof_closure", []), doc.get("isa_partof_closure_label", []))
    ):
        if parent_id != id:
            parent_iri = converter.expand(parent_id)
            collated_results.append({"GO": parent_iri, "label": parent_label, "hierarchy": "parent"})

    collated_results.append({"GO": query_term_iri, "label": doc.get("annotation_class_label", ""), "hierarchy": "query"})

    query_filters = ""
    where_statement = "*:*&fq=isa_partof_closure:" + '"' + id + '"'
    fields_children = "id,annotation_class_label"
    optionals = "&rows=10000"
    children_data = gu_run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.ONTOLOGY, where_statement, query_filters, fields_children, optionals, False
    )

    for child in children_data:
        child_id = child.get("id", "")
        if child_id != id:
            child_iri = converter.expand(child_id)
            collated_results.append({
                "GO": child_iri,
                "label": child.get("annotation_class_label", ""),
                "hierarchy": "child"
            })

    return collated_results


@router.get(
    "/api/go/{id}/models",
    tags=["ontology"],
    description="Returns GO-CAM model identifiers for a given GO term ID, e.g. GO:0008150",
)
async def get_gocam_models_by_go_id(
    id: str = Path(..., description="A GO-Term ID(e.g. GO:0008150 ...)", example="GO:0008150")
):
    """
    Returns GO-CAM model identifiers for a given GO term ID.

    :param id: A GO-Term ID(e.g. GO:0008150 ...)
    :return: GO-CAM model identifiers for a given GO term ID.
    """
    try:
        ontology_utils.is_valid_goid(id)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    cmaps = get_prefixes("go")
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    converter = Converter.from_prefix_map(cmaps, strict=False)
    id = converter.expand(id)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        SELECT distinct ?gocam ?title
        WHERE
        {
            GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .
                ?entity rdf:type owl:NamedIndividual .
                ?entity rdf:type ?goid .
                ?gocam dc:title ?title .
                FILTER(?goid = <%s>)
            }
        }
    """
        % id
    )
    logger.info(query)
    results = si._sparql_query(query)
    transformed_results = transform_array(results)
    return transformed_results
