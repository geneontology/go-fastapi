import logging
import json
from ontobio.sparql.sparql_ontol_utils import run_sparql_on, EOntology, transform, transformArray
from ontobio.golr.golr_query import run_solr_on, replace
from ontobio.io.ontol_renderers import OboJsonGraphRenderer
import app.utils.ontology.ontology_utils as ontology_utils
from typing import List
from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import run_solr_text_on, ESOLR, ESOLRDoc
from enum import Enum

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()

# Some query parameters & parsers
IS_A = "isa"
IS_A_PART_OF = "isa_partof"
REGULATES = "regulates"
TOPOLOGY = "topology_graph"
REGULATES_TRANSITIVITY = "regulates_transitivity_graph"
NEIGHBORHOOD_GRAPH = "neighborhood_graph"
NEIGHBORHOOD_LIMITED_GRAPH = "neighborhood_limited_graph"


class GraphType(str, Enum):
    topology_graph = TOPOLOGY
    regulates_transitivity_graph = REGULATES_TRANSITIVITY
    neighborhood_graph = NEIGHBORHOOD_GRAPH


class RelationshipType(str, Enum):
    IS_A = IS_A
    IS_A_PART_OF = IS_A_PART_OF
    REGULATES = REGULATES


@router.get("/api/ontology/term/{id}", tags=["ontology"])
async def get_term_metadata_by_id(id: str):
    """
    Returns meta data of an ontology term, e.g. GO:0003677
    """
    print(id)
    query = ontology_utils.create_go_summary_sparql(id)
    results = run_sparql_on(query, EOntology.GO)
    return transform(results[0], ['synonyms', 'relatedSynonyms', 'alternativeIds', 'xrefs', 'subsets'])


@router.get("/api/ontology/term/{id}/graph", tags=["ontology"])
async def get_term_graph_by_id(id: str, graph_type: GraphType = Query(GraphType.topology_graph)):
    """
        Returns graph of an ontology term
        """

    graph_type = graph_type + "_json"  # GOLR field names
    print(graph_type)

    data = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, id, graph_type)
    # step required as these graphs are stringified in the json
    data[graph_type] = json.loads(data[graph_type])

    return data


@router.get("/api/ontology/term/{id}/subgraph", tags=["ontology"])
async def get_subgraph_by_term_id(id: str,
                                  cnode: str = Query(None, include_in_schema=False),
                                  include_ancestors: bool = Query(True, include_in_schema=False),
                                  include_descendants: bool = Query(True, include_in_schema=False),
                                  relation: List[str] = Query(['subClassOf', 'BFO:0000050'], include_in_schema=False),
                                  include_meta: bool = Query(False, include_in_schema=False)
                                  ):
    """
        Extract a subgraph from an ontology term
        """
    qnodes = [id]
    if cnode is not None:
        qnodes += cnode

    # COMMENT: based on the CURIE of the id, we should be able to find out the ontology automatically
    ont = ontology_utils.get_ontology("go")
    relations = relation
    print("Traversing: {} using {}".format(qnodes, relations))
    nodes = ont.traverse_nodes(qnodes,
                               up=include_ancestors,
                               down=include_descendants,
                               relations=relations)

    subont = ont.subontology(nodes, relations=relations)
    # TODO: meta is included regardless of whether include_meta is True or False
    ojr = OboJsonGraphRenderer(include_meta=include_meta)
    json_obj = ojr.to_json(subont, include_meta=include_meta)
    return json_obj


@router.get("/api/ontology/term/{id}/subsets", tags=["ontology"])
async def get_subsets_by_term(id: str):
    """
        Returns subsets (slims) associated to an ontology term
        """
    query = ontology_utils.get_go_subsets_sparql_query(id)
    results = run_sparql_on(query, EOntology.GO)
    results = transformArray(results, [])
    results = replace(results, "subset", "OBO:go#", "")
    return results


@router.get("/api/ontology/subset/{id}", tags=["ontology"])
async def get_subset_metadata_by_id(id: str):
    """
        Returns meta data of an ontology subset (slim)
        id is the name of a slim subset, e.g., goslim_agr, goslim_generic
        """

    q = "*:*"
    qf = ""
    fq = "&fq=subset:" + id + "&rows=1000"
    fields = "annotation_class,annotation_class_label,description,source"

    # This is a temporary fix while waiting for the PR of the AGR slim on go-ontology
    if id == "goslim_agr":

        terms_list = set()
        for section in ontology_utils.agr_slim_order:
            terms_list.add(section['category'])
            for term in section['terms']:
                terms_list.add(term)

        goslim_agr_ids = "\" \"".join(terms_list)
        fq = "&fq=annotation_class:(\"" + goslim_agr_ids + "\")&rows=1000"

    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq)

    tr = {}
    for term in data:
        source = term['source']
        if source not in tr:
            tr[source] = {"annotation_class_label": source, "terms": []}
        ready_term = term.copy()
        del ready_term["source"]
        tr[source]["terms"].append(ready_term)

    cats = []
    for category in tr:
        cats.append(category)

    fq = "&fq=annotation_class_label:(" + " or ".join(cats) + ")&rows=1000"
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq)

    for category in tr:
        for temp in data:
            if temp["annotation_class_label"] == category:
                tr[category]["annotation_class"] = temp["annotation_class"]
                tr[category]["description"] = temp["description"]
                break

    result = []
    for category in tr:
        cat = tr[category]
        result.append(cat)

        # if goslim_agr, reorder the list based on the temporary json object below
    if id == "goslim_agr":
        temp = []
        for agr_category in ontology_utils.agr_slim_order:
            cat = agr_category['category']
            for category in result:
                if category['annotation_class'] == cat:
                    ordered_terms = []
                    for ot in agr_category['terms']:
                        for uot in category['terms']:
                            if uot['annotation_class'] == ot:
                                ordered_terms.append(uot)
                                break
                    category["terms"] = ordered_terms
                    temp.append(category)
        result = temp

    return result


@router.get("/api/ontology/shared/{subject}/{object}", tags=["ontology"])
async def get_ancestors_shared_by_two_terms(subject: str, object: str):
    """
        Returns the ancestor ontology terms shared by two ontology terms

        subject: 'CURIE identifier of a GO term, e.g. GO:0006259'
        object: 'CURIE identifier of a GO term, e.g. GO:0046483'
        """

    print(subject)
    print(object)
    fields = "isa_partof_closure,isa_partof_closure_label"

    subres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, subject, fields)
    objres = run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, object, fields)

    print("SUBJECT: ", subres)
    print("OBJECT: ", objres)

    shared = []
    shared_labels = []
    for i in range(0, len(subres['isa_partof_closure'])):
        sub = subres['isa_partof_closure'][i]
        found = False
        if sub in objres['isa_partof_closure']:
            found = True
        if found:
            shared.append(sub)
            shared_labels.append(subres['isa_partof_closure_label'][i])
    return {"goids": shared, "gonames: ": shared_labels}
