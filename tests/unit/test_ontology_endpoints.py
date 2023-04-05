import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("id", go_ids)
def test_term_id_endpoint(id):
    response = test_client.get(f"/api/ontology/term/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_term_subsets_endpoint(id):
    response = test_client.get(f"/api/ontology/term/{id}/subsets")
    assert response.status_code == 200


@pytest.mark.parametrize("id", subsets)
def test_term_by_subset_endpoint(id):
    response = test_client.get(f"/api/ontology/subset/{id}")
    assert response.status_code == 200


def test_ontology_ancestors_shared_sub_obj():
    subject = "GO:0006259"
    object = "GO:0046483"
    response = test_client.get(f"/api/ontology/shared/{subject}/{object}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", subsets)
def test_ontology_subset(id):
    response = test_client.get(f"/api/ontology/subset/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_id(id):
    response = test_client.get(f"/api/ontology/term/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_graph(id):
    response = test_client.get(f"/api/ontology/term/{id}/subgraph")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_subgraph(id):
    data = {"graph_type": "topology_graph"}
    response = test_client.get(f"/api/ontology/term/{id}/graph", params=data)
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_subsets(id):
    response = test_client.get(f"/api/ontology/term/{id}/subsets")
    assert response.status_code == 200
