import json
import logging
from enum import Enum
from typing import List
from pprint import pprint
from fastapi import APIRouter, Query
from ontobio.golr.golr_query import replace
from ontobio.io.ontol_renderers import OboJsonGraphRenderer
from ontobio.sparql.sparql_ontol_utils import (transform, transformArray)

from linkml_runtime.utils.namespaces import Namespaces
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from oaklib.implementations.sparql.sparql_query import SparqlQuery
from ontobio.util.user_agent import get_user_agent

import app.utils.ontology.ontology_utils as ontology_utils
from app.utils.golr.golr_utls import run_solr_on, run_solr_text_on
from app.utils.settings import ESOLRDoc, ESOLR

logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()


@router.get("/api/pmid/{id}/models", tags=["publications"])
async def get_model_details_by_pmid(id: str = Query(
    None, description="A PMID (e.g. 15314168 or 26954676)")):
    """
    Returns models for a given PMID
    """
    ns = Namespaces()
    ns.add_prefixmap('go')
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
    si = SparqlImplementation(ont_r)

    query = """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
		SELECT distinct ?gocam
        WHERE 
        {
	        GRAPH ?gocam {
    	        ?gocam metago:graphType metago:noctuaCam .    	
        	    ?s dc:source ?source .
            	BIND(REPLACE(?source, " ", "") AS ?source) .
	            FILTER((CONTAINS(?source, \"""" + id + """\")))
    	    }           
        }
    """
    results = si._query(query)
    collated_results = []
    collated = {}
    for result in results:
        collated["gocam"] = result["gocam"].get("value")
        collated_results.append(collated)
    return collated_results