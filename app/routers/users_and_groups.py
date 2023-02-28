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


@router.get("/api/users", tags=["users and groups"])
async def get_model_by_start_size():
    """
    Returns meta data of all GO users
    """
    ns = Namespaces()
    ns.add_prefixmap('go')
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
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
    results = si._query(query)
    results = transformArray(results, ["organizations", "affiliations"])
    return results