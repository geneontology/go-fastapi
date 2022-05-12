import logging
import json
from ontobio.sparql.sparql_ontol_utils import run_sparql_on, EOntology, transform, transformArray
from ontobio.golr.golr_query import run_solr_on, replace
from ontobio.io.ontol_renderers import OboJsonGraphRenderer
from ..utils.ontology.ontology_manager import get_ontology
from prefixcommons.curie_util import get_prefixes, expand_uri, contract_uri

from typing import List
from fastapi import APIRouter, Query
from .slimmer import gene_to_uniprot_from_mygene
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import run_solr_text_on, ESOLR, ESOLRDoc

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


@router.post("/identifier/prefixes", tags=["identifier/prefixes"])
async def get_all_prefixes():
        """
        Returns list of prefixes
        """
        return get_prefixes()


@router.post("/identifier/prefixes/expand/{id}", tags=["identifier/prefixes"])
async def get_all_prefixes(id: str):
        """
        Returns expanded URI
        id: ID of entity to be contracted to URI, e.g "MGI:1"
        """
        return expand_uri(id)


@router.post("/identifier/prefixes/contract/{uri}", tags=["identifier/prefixes"])
async def get_all_prefixes(uri: str):
        """
        Returns contracted URI
        uri: URI of entity to be contracted to identifier/CURIE, e.g "http://www.informatics.jax.org/accession/MGI:1"
        """
        return contract_uri(uri)
    

    
    

