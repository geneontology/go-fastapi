import logging
from fastapi import APIRouter, Query
from linkml_runtime.utils.namespaces import Namespaces
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from pprint import pprint
from oaklib.resource import OntologyResource
from ontobio.util.user_agent import get_user_agent

logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()


@router.get("/api/pmid/{id}/models", tags=["publications"])
async def get_model_details_by_pmid(
    id: str = Query(None, description="A PMID (e.g. 15314168 or 26954676)")
):
    """
    Returns models for a given PMID
    """
    ns = Namespaces()
    ns.add_prefixmap("go")
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
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
