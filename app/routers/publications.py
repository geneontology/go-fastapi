import logging
from pprint import pprint

from fastapi import APIRouter, Query
from oaklib.implementations.sparql.sparql_implementation import \
    SparqlImplementation
from oaklib.resource import OntologyResource

from app.utils.settings import get_sparql_endpoint, get_user_agent

logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()


@router.get("/api/pmid/{id}/models", tags=["publications"])
async def get_model_details_by_pmid(
    id: str = Query(None, description="A PMID (e.g. 15314168 or 26954676)")
):
    """
    Returns models for a given PMID
    """
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)

    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT distinct ?gocam
        WHERE 
        {
            GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .    	
                ?s dc:source ?source .
                BIND(REPLACE(?source, " ", "") AS ?source) .
                FILTER((CONTAINS(?source, \""""
        + id
        + """\")))
            }           
        }
    """
    )
    results = si._sparql_query(query)

    pprint(results)
    collated_results = []
    collated = {}
    for result in results:
        print(result)
        collated["gocam"] = result["gocam"].get("value")
        collated_results.append(collated)
    return results
