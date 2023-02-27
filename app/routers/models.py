import json
import logging
from enum import Enum
from typing import List

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

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()

@router.get("/api/models", tags=["models"])
async def get_model_by_start_size(start: int, size: int, last: int = None):
    """
    Returns meta data of an ontology term, e.g. GO:0003677
    """
    ns = Namespaces()
    ns.add_prefixmap('go')
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
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
    results = si._query(query)
    results = transformArray(results, ["orcids", "names", "groupids", "groupnames"])
    return results