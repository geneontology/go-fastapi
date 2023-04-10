import logging
from fastapi import APIRouter, Query
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from app.utils.settings import get_sparql_endpoint, get_user_agent
from app.utils.sparql.sparql_utils import transform_array

logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()


@router.get("/api/users", tags=["users and groups"], deprecated=True)
async def get_users():
    """
    DEPRECATED
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
    return results


@router.get("/api/groups", tags=["users and groups"], deprecated=True)
async def get_groups():
    """
    DEPRECATED
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
    return results


@router.get("/api/groups/{name}", tags=["users and groups"], deprecated=True)
async def get_group_metadata_by_name(
    name: str = Query(
        None, description="The name of the Group (e.g. SynGO, GO Central, MGI, ...)"
    )
):
    """
    DEPRECATED
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
            PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>
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
        collated["orcide"] = result["orcid"].get("value")
        collated["gocams"] = result["gocams"].get("value")
        collated["bps"] = result["bps"].get("value")
        collated_results.append(collated)
    return collated_results
