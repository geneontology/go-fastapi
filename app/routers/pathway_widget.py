import logging

from fastapi import APIRouter, Query
from oaklib.implementations.sparql.sparql_implementation import \
    SparqlImplementation
from oaklib.resource import OntologyResource
from prefixcommons.curie_util import expand_uri, read_biocontext
from app.utils.settings import get_sparql_endpoint, get_user_agent
logger = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
SPARQL_ENDPOINT = get_sparql_endpoint()
router = APIRouter()


@router.get("/api/gp/{id}/models", tags=["bioentity"])
async def get_gocams_by_geneproduct_id(
    id: str = Query(
        None,
        description="A Gene Product CURIE (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)",
    ),
    causalmf: int = Query(
        None,
        description="Used by the pathway widget to get GP models with 2 causal MFs",
        include_in_schema=False,
    ),
):
    """
    Returns GO-CAM models associated with a given Gene Product identifier (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)
    """

    cmaps = [read_biocontext("go_context")]
    for d in cmaps:
        d.update((k, "http://identifiers.org/mgi/MGI:") for k, v in d.items() if v == "http://identifiers.org/mgi/")
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    id = expand_uri(id=id, cmaps=cmaps)
    logger.info(
        "reformatted curie into IRI using identifiers.org from api/gp/{id}/models endpoint",
        id,
    )
    query = (
        """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>

            SELECT distinct ?gocam ?title

            WHERE 
            {

              GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .    
                ?s enabled_by: ?gpnode .    
                ?gpnode rdf:type ?identifier .
                ?gocam dc:title ?title .   
                FILTER(?identifier = <%s>) .            
              }

            }
            ORDER BY ?gocam

        """
        % id
    )
    if causalmf == 2:
        query = (
            """
      PREFIX pr: <http://purl.org/ontology/prv/core#>
      PREFIX metago: <http://model.geneontology.org/>
      PREFIX dc: <http://purl.org/dc/elements/1.1/>
      PREFIX providedBy: <http://purl.org/pav/providedBy>
      PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
      PREFIX causally_upstream_of_or_within: <http://purl.obolibrary.org/obo/RO_0002418>
      PREFIX causally_upstream_of_or_within_negative_effect: <http://purl.obolibrary.org/obo/RO_0004046>
      PREFIX causally_upstream_of_or_within_positive_effect: <http://purl.obolibrary.org/obo/RO_0004047>
      PREFIX causally_upstream_of: <http://purl.obolibrary.org/obo/RO_0002411>
      PREFIX causally_upstream_of_negative_effect: <http://purl.obolibrary.org/obo/RO_0002305>
      PREFIX causally_upstream_of_positive_effect: <http://purl.obolibrary.org/obo/RO_0002304>
      PREFIX regulates: <http://purl.obolibrary.org/obo/RO_0002211>
      PREFIX negatively_regulates: <http://purl.obolibrary.org/obo/RO_0002212>
      PREFIX positively_regulates: <http://purl.obolibrary.org/obo/RO_0002213>
      PREFIX directly_regulates: <http://purl.obolibrary.org/obo/RO_0002578>
      PREFIX directly_positively_regulates: <http://purl.obolibrary.org/obo/RO_0002629>
      PREFIX directly_negatively_regulates: <http://purl.obolibrary.org/obo/RO_0002630>
      PREFIX directly_activates: <http://purl.obolibrary.org/obo/RO_0002406>
      PREFIX indirectly_activates: <http://purl.obolibrary.org/obo/RO_0002407>
      PREFIX directly_inhibits: <http://purl.obolibrary.org/obo/RO_0002408>
      PREFIX indirectly_inhibits: <http://purl.obolibrary.org/obo/RO_0002409>
      PREFIX transitively_provides_input_for: <http://purl.obolibrary.org/obo/RO_0002414>
      PREFIX immediately_causally_upstream_of: <http://purl.obolibrary.org/obo/RO_0002412>
      PREFIX directly_provides_input_for: <http://purl.obolibrary.org/obo/RO_0002413>
      PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
      PREFIX hint: <http://www.bigdata.com/queryHints#>
      SELECT DISTINCT ?gocam ?title
      WHERE {
        GRAPH ?gocam  {  
          # Inject gene product ID here
          ?gene rdf:type <%s> .
        }
        FILTER EXISTS {
          ?gocam metago:graphType metago:noctuaCam .
        }
        ?gocam dc:title ?title .
        FILTER (
          EXISTS {  
            GRAPH ?gocam  {      ?ind1 enabled_by: ?gene . }
            GRAPH ?gocam { ?ind1 ?causal1 ?ind2 } 
            ?causal1 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind1 causally_upstream_of_or_within: ?ind2 . 
            GRAPH ?gocam  {       ?ind2 enabled_by: ?gpnode2 . }
            GRAPH ?gocam { ?ind2 ?causal2 ?ind3 }
            ?causal2 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind2 causally_upstream_of_or_within: ?ind3 . 
            GRAPH ?gocam  {       ?ind3 enabled_by: ?gpnode3 . }
            FILTER(?gene != ?gpnode2) 
            FILTER(?gene != ?gpnode3) 
            FILTER(?gpnode2 != ?gpnode3)
          } ||  
          EXISTS {          
            GRAPH ?gocam  {       ?ind1 enabled_by: ?gpnode1 . }
            GRAPH ?gocam { ?ind1 ?causal1 ?ind2 } 
            ?causal1 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind1 causally_upstream_of_or_within: ?ind2 . 
            GRAPH ?gocam  {          ?ind2 enabled_by: ?gene . }
            GRAPH ?gocam { ?ind2 ?causal2 ?ind3 }
            ?causal2 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind2 causally_upstream_of_or_within: ?ind3 . 
            GRAPH ?gocam  {           ?ind3 enabled_by: ?gpnode3 . }
            FILTER(?gpnode1 != ?gene) 
            FILTER(?gpnode1 != ?gpnode3) 
            FILTER(?gene != ?gpnode3)
          } ||
          EXISTS {
            GRAPH ?gocam  {       ?ind1 enabled_by: ?gpnode1 . }
            GRAPH ?gocam { ?ind1 ?causal1 ?ind2 } 
            ?causal1 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind1 causally_upstream_of_or_within: ?ind2 . 
            GRAPH ?gocam  {           ?ind2 enabled_by: ?gpnode2 . }
            GRAPH ?gocam { ?ind2 ?causal2 ?ind3 }
            ?causal2 rdfs:subPropertyOf* causally_upstream_of_or_within: .
            ?ind2 causally_upstream_of_or_within: ?ind3 . 
            GRAPH ?gocam  {         ?ind3 enabled_by: ?gene . }
            FILTER(?gpnode1 != ?gpnode2) 
            FILTER(?gpnode1 != ?gene) 
            FILTER(?gpnode2 != ?gene)
          }
        )
      }
      ORDER BY ?gocam
    """
            % id
        )
    results = si._sparql_query(query)
    collated_results = []
    collated = {}
    for row in results:
        collated["gocam"] = row["gocam"].get("value")
        collated["title"] = row["title"].get("value")
        collated_results.append(collated)
    return results
