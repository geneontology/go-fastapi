"""Ontology-related endpoints."""
import json
import logging
from enum import Enum
from typing import List

from curies import Converter
from fastapi import APIRouter, Query, Path
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from ontobio.io.ontol_renderers import OboJsonGraphRenderer

import app.utils.ontology.ontology_utils as ontology_utils
from app.utils.golr.golr_utils import run_solr_on, run_solr_text_on
from app.utils.prefixes.prefix_utils import get_prefixes
from app.utils.settings import ESOLR, ESOLRDoc, get_sparql_endpoint, get_user_agent
from app.utils.sparql.sparql_utils import transform, transform_array

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()


class GraphType(str, Enum):
    """
    Enum for the different types of graphs that can be returned.

    """
    topology_graph = "topology_graph"


@router.get("/api/ontology/term/{id}", tags=["ontology"])
async def get_term_metadata_by_id(id: str = Path(..., description="The ID of the term to extract the metadata from,  "
                                                                  "e.g. GO:0003677")):
    """
    Returns metadata of an ontology term, e.g. GO:0003677.

    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = ontology_utils.create_go_summary_sparql(id)
    results = si._sparql_query(query)
    return transform(
        results[0],
        ["synonyms", "relatedSynonyms", "alternativeIds", "xrefs", "subsets"],
    )


@router.get("/api/ontology/term/{id}/graph", tags=["ontology"])
async def get_term_graph_by_id(
        id: str = Path(..., description="The ID of the term to extract the graph from,  e.g. GO:0003677"),
        graph_type: GraphType = Query(GraphType.topology_graph)
):
    """
    Returns graph of an ontology term.

    """
    graph_type = graph_type + "_json"  # GOLR field names
    log.info(graph_type)

    data = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, graph_type)
    # step required as these graphs are made into strings in the json
    data[graph_type] = json.loads(data[graph_type])

    return data


@router.get("/api/ontology/term/{id}/subgraph", tags=["ontology"])
async def get_subgraph_by_term_id(
    id: str = Path(..., description="The ID of the term to extract the subgraph from,  e.g. GO:0003677"),
    cnode: str = Query(None, include_in_schema=False),
    include_ancestors: bool = Query(True, include_in_schema=False),
    include_descendants: bool = Query(True, include_in_schema=False),
    relation: List[str] = Query(["subClassOf", "BFO:0000050"], include_in_schema=False),
    include_meta: bool = Query(False, include_in_schema=False),
):
    """
    Extract a subgraph from an ontology term. e.g. GO:0003677.

    """
    qnodes = [id]
    if cnode is not None:
        qnodes += cnode

    # COMMENT: based on the CURIE of the id, we should be able to find out the ontology automatically
    ont = ontology_utils.get_ontology("go")
    relations = relation
    log.info("Traversing: {} using {}".format(qnodes, relations))
    nodes = ont.traverse_nodes(qnodes, up=include_ancestors, down=include_descendants, relations=relations)

    subont = ont.subontology(nodes, relations=relations)

    # TODO: meta is included regardless of whether include_meta is True or False

    ojr = OboJsonGraphRenderer(include_meta=include_meta)
    json_obj = ojr.to_json(subont, include_meta=include_meta)

    return json_obj


@router.get("/api/ontology/term/{id}/subsets", tags=["ontology"])
async def get_subsets_by_term(
        id: str = Path(..., description="The ID of the term to extract the subgraph from,  e.g. GO:0003677")):
    """
    Returns subsets (slims) associated to an ontology term.

    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = ontology_utils.get_go_subsets_sparql_query(id)
    results = si._sparql_query(query)
    results = transform_array(results, [])
    results = (results, "subset", "OBO:go#", "")
    return results


@router.get("/api/ontology/shared/{subject}/{object}", tags=["ontology"])
async def get_ancestors_shared_by_two_terms(
        subject: str = Path(..., description="'CURIE identifier of a GO term, e.g. GO:0006259'"),
        object: str = Path(..., description="'CURIE identifier of a GO term, e.g. GO:0046483'")
):
    """
    Returns the ancestor ontology terms shared by two ontology terms.

    subject: 'CURIE identifier of a GO term, e.g. GO:0006259'
    object: 'CURIE identifier of a GO term, e.g. GO:0046483'
    """
    log.info(subject)
    log.info(object)
    fields = "isa_partof_closure,isa_partof_closure_label"

    subres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, subject, fields)
    objres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, object, fields)

    log.info("SUBJECT: ", subres)
    log.info("OBJECT: ", objres)

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


@router.get("/api/go/{id}", tags=["ontology"])
async def get_go_term_detail_by_go_id(
    id: str = Path(None, description="A GO-Term ID(e.g. GO:0005885, GO:0097136 ...)")
):
    """
    Returns models for a given GO term ID.

    e.g. GO:0008150
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = ontology_utils.create_go_summary_sparql(id)
    results = si._sparql_query(query)
    return transform(
        results[0],
        ["synonyms", "relatedSynonyms", "alternativeIds", "xrefs", "subsets"],
    )


@router.get("/api/go/{id}/hierarchy", tags=["ontology"])
async def get_go_hierarchy_go_id(id: str = Path(None, description="A GO-Term ID(e.g. GO:0005885, GO:0097136 ...)")):
    """
    Returns parent and children relationships for a given GO ID.

    e.g. GO:0005885
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    cmaps = get_prefixes("go")
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    converter = Converter.from_prefix_map(cmaps, strict=False)
    id = converter.expand(id)

    query = (
        """
        PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
        SELECT ?hierarchy ?GO ?label WHERE {
            BIND(<%s> as ?goquery)
            {
                {
                    ?goquery rdfs:subClassOf+ ?GO .
                    ?GO rdfs:label ?label .
                    FILTER (LANG(?label) != "en")
                    BIND("parent" as ?hierarchy)
                    }
                UNION
                {
                    ?GO rdfs:subClassOf* ?goquery .
                    ?GO rdfs:label ?label .
                    FILTER (LANG(?label) != "en")
                    BIND(IF(?goquery = ?GO, "query", "child") as ?hierarchy) .
                }
            }
        }
    """
        % id
    )
    results = si._sparql_query(query)
    collated_results = []
    collated = {}
    for result in results:
        collated["GO"] = result["GO"].get("value")
        collated["label"] = result["label"].get("value")
        collated["hierarchy"] = result["hierarchy"].get("value")
        collated_results.append(collated)
    return collated_results


@router.get("/api/go/{id}/models", tags=["ontology"])
async def get_gocam_models_by_go_id(id: str = Path(None, description="A GO-Term ID(e.g. GO:0005885, GO:0097136 ...)")):
    """
    Returns parent and children relationships for a given GO ID, e.g. GO:0005885.

    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    cmaps = get_prefixes("go")
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    converter = Converter.from_prefix_map(cmaps, strict=False)
    id = converter.expand(id)
    print(id)
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
    results = si._sparql_query(query)
    return transform_array(results)
