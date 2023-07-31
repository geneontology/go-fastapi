import logging
from pprint import pprint

from fastapi.testclient import TestClient

from app.main import app
from app.utils.settings import ESOLR, ESOLRDoc

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


def test_golr_solr():
    assert ESOLR.GOLR.value == "https://golr-aux.geneontology.io/solr/"
    assert ESOLRDoc.ONTOLOGY.value == "ontology_class"


def test_search_entity_ssh():
    data = {"category": "gene"}
    response = test_client.get("/api/search/entity/autocomplete/ssh", params=data)
    assert response.status_code == 200


def test_autocomplete_shh():
    data = {"category": "gene"}
    response = test_client.get("/api/search/entity/autocomplete/shh", params=data)
    assert "id" in response.json().get("docs")[0]
    assert response.status_code == 200


def test_autocomplete_biological():
    response = test_client.get("/api/search/entity/autocomplete/biological")
    assert "id" in response.json().get("docs")[0]
    pprint(response.json())
    assert response.status_code == 200


def test_autocomplete_go():
    response = test_client.get("/api/search/entity/autocomplete/go")
    assert "id" in response.json().get("docs")[0]
    assert response.status_code == 200
