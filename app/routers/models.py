"""Model API router."""
import logging
from typing import List

from fastapi import APIRouter, Path, Query
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource

from app.utils.settings import get_sparql_endpoint, get_user_agent
from app.utils.sparql_utils import transform_array

logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
SPARQL_ENDPOINT = get_sparql_endpoint()
router = APIRouter()


@router.get("/api/models", tags=["models"], deprecated=True)
async def get_model_by_start_size(
        start: int = Query(None, description="start"),
        size: int = Query(None, description="Number of models to look for")
):
    """Returns metadata of an ontology term, e.g. GO:0003677."""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>
        PREFIX providedBy: <http://purl.org/pav/providedBy>

        SELECT  ?gocam ?date ?title (GROUP_CONCAT(distinct ?orcid;separator="@|@") AS ?orcids)
                                    (GROUP_CONCAT(distinct ?name;separator="@|@") AS ?names)
                                    (GROUP_CONCAT(distinct ?providedBy;separator="@|@") AS ?groupids)
                                    (GROUP_CONCAT(distinct ?providedByLabel;separator="@|@") AS ?groupnames)
        WHERE
        {
            {
                GRAPH ?gocam {
                    ?gocam metago:graphType metago:noctuaCam .
                    ?gocam dc:title ?title ;
                        dc:date ?date ;
                        dc:contributor ?orcid ;
                        providedBy: ?providedBy .

                    BIND( IRI(?orcid) AS ?orcidIRI ).
                    BIND( IRI(?providedBy) AS ?providedByIRI ).
                }

                optional {
                    ?providedByIRI rdfs:label ?providedByLabel .
                }
                optional { ?orcidIRI rdfs:label ?name }
                BIND(IF(bound(?name), ?name, ?orcid) as ?name) .
            }

        }
        GROUP BY ?gocam ?date ?title
        ORDER BY DESC(?date)
        """
    if size:
        query += "\nLIMIT " + str(size)
    if start:
        query += "\nOFFSET " + str(start)
    results = si._sparql_query(query)
    results = transform_array(results, ["orcids", "names", "groupids", "groupnames"])
    return results


@router.get("/api/models/go", tags=["models"])
async def get_goterms_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        example=["581e072c00000295","SYNGO_369"]
    )
):
    """Returns go term details based on a GO-CAM model ID."""
    gocam = ""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    for model in gocams:
        if gocam == "":
            gocam = "<http://model.geneontology.org/" + model + "> "
        else:
            gocam = gocam + "<http://model.geneontology.org/" + model + "> "
    query = (
        """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
            PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
            PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
            PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
            SELECT distinct ?gocam ?goclasses ?goids ?gonames ?definitions
            WHERE
            {
                VALUES ?gocam { %s }
                GRAPH ?gocam {
                    ?entity rdf:type owl:NamedIndividual .
                    ?entity rdf:type ?goids
                }

                VALUES ?goclasses { BP: MF: CC:  } .
                ?goids rdfs:subClassOf+ ?goclasses .
                ?goids rdfs:label ?gonames .
                ?goids definition: ?definitions .
            }
            ORDER BY DESC(?gocam)
    """
        % gocam
    )
    results = si._sparql_query(query)
    summary_gocam = ""
    collated = {}
    collated_results = []
    for result in results:
        if summary_gocam == "":
            collated["goclasses"] = [result["goclasses"].get("value")]
            collated["goids"] = [result["goids"].get("value")]
            collated["gonames"] = [result["gonames"].get("value")]
            collated["definitions"] = [result["definitions"].get("value")]
            collated["gocam"] = result["gocam"].get("value")
            summary_gocam = result["gocam"].get("value")
        elif summary_gocam == result["gocam"].get("value"):
            collated["goclasses"].append(result["goclasses"].get("value"))
            collated["goids"].append(result["goids"].get("value"))
            collated["gonames"].append(result["gonames"].get("value"))
            collated["definitions"].append(result["definitions"].get("value"))
        else:
            collated_results.append(collated)
            collated = {}
            summary_gocam = result["gocam"].get("value")
            collated["goclasses"] = [result["goclasses"].get("value")]
            collated["goids"] = [result["goids"].get("value")]
            collated["gonames"] = [result["gonames"].get("value")]
            collated["definitions"] = [result["definitions"].get("value")]
            collated["gocam"] = result["gocam"].get("value")
    collated_results.append(collated)
    return collated_results


@router.get("/api/models/gp", tags=["models"])
async def get_geneproducts_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        example=["581e072c00000295","SYNGO_369"]
    )
):
    """Returns gene product details based on a GO-CAM model ID."""
    gocam = ""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    for model in gocams:
        if gocam == "":
            gocam = "<http://model.geneontology.org/" + model + "> "
        else:
            gocam = gocam + "<http://model.geneontology.org/" + model + "> "
    query = (
        """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
            PREFIX in_taxon: <http://purl.obolibrary.org/obo/RO_0002162>
            SELECT ?gocam   (GROUP_CONCAT(distinct ?identifier;separator="@|@") as ?gpids)
                            (GROUP_CONCAT(distinct ?name;separator="@|@") as ?gpnames)
            WHERE
            {
                VALUES ?gocam { %s }

                GRAPH ?gocam {
                    ?s enabled_by: ?gpnode .
                    ?gpnode rdf:type ?identifier .
                    FILTER(?identifier != owl:NamedIndividual) .
                }
                optional {
                    GRAPH <http://purl.obolibrary.org/obo/go/extensions/go-graphstore.owl> {
                        ?identifier rdfs:label ?name
                    }
                }
            }
            GROUP BY ?gocam
    """
        % gocam
    )
    results = si._sparql_query(query)
    results = transform_array(results, ["gpids", "gpnames"])
    return results


@router.get("/api/models/pmid", tags=["models"])
async def get_publication_details_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        example=["581e072c00000295", "SYNGO_369"]
    )
):
    """Returns pubmed details based on a GO-CAM model ID."""

    gocam = ""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    for model in gocams:
        if gocam == "":
            gocam = "<http://model.geneontology.org/" + model + "> "
        else:
            gocam = gocam + "<http://model.geneontology.org/" + model + "> "
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>

        SELECT  distinct ?gocam (GROUP_CONCAT(distinct ?source; separator="@|@") as ?sources)
        WHERE
        {
            values ?gocam { %s }
            GRAPH ?gocam {
                ?s dc:source ?source .
                BIND(REPLACE(?source, " ", "") AS ?source) .
                FILTER((CONTAINS(?source, "PMID")))
            }
        }
        GROUP BY ?gocam

    """
        % gocam
    )
    results = si._sparql_query(query)
    return results


@router.get("/api/models/{id}", tags=["models"])
async def get_term_details_by_model_id(
    id: str = Path(
        ...,
        description="A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)",
        example="581e072c00000295"
    )
):
    """Returns model details based on a GO-CAM model ID."""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>

        SELECT ?subject ?predicate ?object
        WHERE
        {
            GRAPH metago:%s {
                ?subject ?predicate ?object
            }
        }
    """
        % id
    )
    results = si._sparql_query(query)
    collated_results = []
    for result in results:
        collated = {
            "subject": result["subject"].get("value"),
            "predicate": result["predicate"].get("value"),
            "object": result["object"].get("value"),
        }
        collated_results.append(collated)
    return collated_results
