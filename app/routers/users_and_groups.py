"""The users and groups endpoints."""

import logging

from fastapi import APIRouter, Path
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.settings import get_sparql_endpoint, get_user_agent
from app.utils.sparql_utils import transform_array

logger = logging.getLogger()

USER_AGENT = get_user_agent()
router = APIRouter()


@router.get("/api/users", tags=["users and groups"], deprecated=True, description="Get GO users.")
async def get_users():
    """
    DEPRECATED.

    Returns metadata of all GO users
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>

        SELECT  ?orcid ?name    (GROUP_CONCAT(distinct ?organization;separator="@|@") AS ?organizations)
                                (GROUP_CONCAT(distinct ?affiliation;separator="@|@") AS ?affiliations)
                                (COUNT(distinct ?cam) AS ?gocams)
        WHERE
        {
            ?cam metago:graphType metago:noctuaCam .
            ?cam dc:contributor ?orcid .

            BIND( IRI(?orcid) AS ?orcidIRI ).

            optional { ?orcidIRI rdfs:label ?name } .
            optional { ?orcidIRI <http://www.w3.org/2006/vcard/ns#organization-name> ?organization } .
            optional { ?orcidIRI has_affiliation: ?affiliation } .

            BIND(IF(bound(?name), ?name, ?orcid) as ?name) .
        }
        GROUP BY ?orcid ?name
        """
    results = si._sparql_query(query)
    results = transform_array(results, ["organizations", "affiliations"])
    if not results:
        return DataNotFoundException(detail="No users found")
    return results


@router.get("/api/users/{orcid}", tags=["models"], description="Get GO-CAM models by ORCID")
async def get_user_by_orcid(
    orcid: str = Path(
        ...,
        description="The ORCID of the user (e.g. 0000-0002-7285-027X)",
        example="0000-0002-7285-027X",
    )
):
    """Returns GO-CAM model identifiers for a particular contributor orcid."""
    mod_orcid = f"https://orcid.org/{orcid}"
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
        PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
        PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
        PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
        PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
        PREFIX biomacromolecule: <http://purl.obolibrary.org/obo/CHEBI_33694>

        SELECT distinct ?title ?contributor ?gocam
WHERE {
    GRAPH ?gocam {
        ?gocam metago:graphType metago:noctuaCam ;
               dc:date ?date ;
               dc:title ?title ;
               dc:contributor ?contributor .


        # Contributor filter
        FILTER(?contributor = "%s")
    }
}
        """
        % mod_orcid
    )

    results = si._sparql_query(query)

    if not results:
        raise DataNotFoundException(detail=f"Item with ID {orcid} not found")
    else:
        collated_results = []
        for result in results:
            collated_results.append({"model_id": result["gocam"].get("value"), "title": result["title"].get("value")})
        return collated_results


@router.get("/api/users/{orcid}/models", tags=["models"])
async def get_models_by_orcid(
    orcid: str = Path(
        ...,
        description="The ORCID of the user (e.g. 0000-0002-7285-027X)",
        example="0000-0002-7285-027X",
    )
):
    """Returns model details based on an orcid."""
    mod_orcid = f'"http://orcid.org/{orcid}"^^xsd:string'
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
        PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
        PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
        PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
        PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
        PREFIX biomacromolecule: <http://purl.obolibrary.org/obo/CHEBI_33694>

        SELECT distinct ?title ?contributor ?gocam
WHERE {
    GRAPH ?gocam {
        ?gocam metago:graphType metago:noctuaCam ;
               dc:date ?date ;
               dc:title ?title ;
               dc:contributor ?contributor .


        # Contributor filter
        FILTER(?contributor = "%s")
    }
}
        """
        % mod_orcid
    )

    results = si._sparql_query(query)

    if not results:
        raise DataNotFoundException(detail=f"Item with ID {orcid} not found")
    else:
        collated_results = []
        for result in results:
            collated_results.append({"model_id": result["gocam"].get("value"), "title": result["title"].get("value")})
        return collated_results


@router.get("/api/users/{orcid}/gp", tags=["models"], description="Get GPs by orcid")
async def get_gp_models_by_orcid(
    orcid: str = Path(
        ...,
        description="The ORCID of the user (e.g. 0000-0002-7285-027X)",
        example="0000-0002-7285-027X",
    )
):
    """Returns GO-CAM model identifiers for a particular contributor orcid."""
    mod_orcid = f'"http://orcid.org/{orcid}"^^xsd:string'
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
        PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
        PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
        PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
        PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
        PREFIX biomacromolecule: <http://purl.obolibrary.org/obo/CHEBI_33694>

        SELECT ?identifier ?name ?species (count(?name) as ?usages)
        (GROUP_CONCAT(?cam;separator="@|@") as ?gocams)
        (GROUP_CONCAT(?date;separator="@|@") as ?dates)
        (GROUP_CONCAT(?title;separator="@|@") as ?titles)
        WHERE
        {
            #BIND("SynGO:SynGO-pim"^^xsd:string as ?orcid) .
            #BIND("http://orcid.org/0000-0001-7476-6306"^^xsd:string as ?orcid)
            #BIND("http://orcid.org/0000-0003-1074-8103"^^xsd:string as ?orcid) .
          	#BIND("http://orcid.org/0000-0001-5259-4945"^^xsd:string as ?orcid) .

            BIND(%s as ?orcid)
            BIND(IRI(?orcid) as ?orcidIRI) .

            # Getting some information on the model
            GRAPH ?cam {
                ?cam metago:graphType metago:noctuaCam .
                ?cam dc:contributor ?orcid .
                ?cam dc:title ?title .
                ?cam dc:date ?date .

                ?s enabled_by: ?id .
                ?id rdf:type ?identifier .
                FILTER(?identifier != owl:NamedIndividual) .
            }

            ?identifier rdfs:label ?name .
            ?identifier rdfs:subClassOf ?v0 .
            ?v0 owl:onProperty <http://purl.obolibrary.org/obo/RO_0002162> .
            ?v0 owl:someValuesFrom ?taxon .
            ?taxon rdfs:label ?species .
        }
        GROUP BY ?identifier ?name ?species
        ORDER BY DESC(?usages)
        """
        % mod_orcid
    )

    results = si._sparql_query(query)
    collated_results = []
    collated = {}
    for result in results:
        collated["gocams"] = result["gocams"].get("value")
        collated["dates"] = result["dates"].get("value")
        collated["titles"] = result["titles"].get("value")
        collated_results.append(collated)
    if not collated_results:
        return DataNotFoundException(detail=f"Item with ID {orcid} not found")
    return collated_results


@router.get("/api/groups", tags=["users and groups"], deprecated=True, description="Get GO groups")
async def get_groups():
    """
    DEPRECATED.

    Returns metadata of a GO group
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
        PREFIX hint: <http://www.bigdata.com/queryHints#>
        SELECT  distinct ?name ?url (COUNT(distinct ?orcidIRI) AS ?members)
                                    (COUNT(distinct ?cam) AS ?gocams)
            WHERE {
                ?cam metago:graphType metago:noctuaCam .
                ?cam dc:contributor ?orcid .
                BIND( IRI(?orcid) AS ?orcidIRI ).
                ?orcidIRI has_affiliation: ?url .
                ?url rdfs:label ?name .
                hint:Prior hint:runLast true .
            }
            GROUP BY ?url ?name
        """
    results = si._sparql_query(query)
    if not results:
        return DataNotFoundException(detail="No groups found")
    return results


@router.get(
    "/api/groups/{name}", tags=["users and groups"], deprecated=True, description="Get GO group metadata by name"
)
async def get_group_metadata_by_name(
    name: str = Path(..., description="The name of the Group (e.g. SynGO, GO Central, MGI, ...)")
):
    """
    DEPRECATED.

    Returns metadata of a GO group
    please note, this endpoint was migrated from the GO-CAM service api and may not be
    supported in its current form in the future.
    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
         PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
            PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
            PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
            PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
            PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>

            SELECT ?url ?orcid ?name   (COUNT(distinct ?gocam) AS ?gocams)
                                                (COUNT(distinct ?goid) AS ?bps)
            WHERE {

            BIND(\""""
        + name
        + """\""""
        + """as ?groupName) .
                    ?url rdfs:label ?groupName .
                    ?orcidIRI has_affiliation: ?url .
                    ?orcidIRI rdfs:label ?name
                GRAPH ?gocam {
                    ?gocam metago:graphType metago:noctuaCam ;
                    dc:contributor ?orcid .
                    BIND(IRI(?orcid) as ?contribIRI) .
                    ?entity rdf:type owl:NamedIndividual .
                    ?entity rdf:type ?goid
                }

            filter(?contribIRI = ?orcidIRI) .
            ?contribIRI rdfs:label ?name .

            ?entity rdf:type BP: .
            filter(?goid != BP: )
            }
            GROUP BY ?url ?orcid ?name

        """
    )
    results = si._sparql_query(query)
    collated_results = []
    collated = {}
    for result in results:
        collated["name"] = result["name"].get("value")
        collated["orcid"] = result["orcid"].get("value")
        collated["gocams"] = result["gocams"].get("value")
        collated["bps"] = result["bps"].get("value")
        collated_results.append(collated)
    if not collated_results:
        return DataNotFoundException(detail=f"Item with ID {name} not found")
    return collated_results
