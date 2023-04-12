import logging
import urllib.parse
from pprint import pprint
from fastapi.testclient import TestClient
import pytest
from app.main import app

test_client = TestClient(app)

gene_ids = ["WB:WBGene00002147", "MGI:3588192", "FB:FBgn0003731"]

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("id", gene_ids)
def test_get_gocams_by_geneproduct_id(id):
    response = test_client.get(f"/api/gp/{id}/models")
    assert len(response.json()) > 0
    assert response.status_code == 200


def test_get_gocams_by_geneproduct_id_MGI():
    response = test_client.get(f"/api/gp/MGI:3588192/models")
    assert len(response.json()) > 0
    assert response.status_code == 200


def test_get_gocams_by_geneproduct_id_WB():
    response = test_client.get(f"/api/gp/WB:WBGene00002147/models")
    assert len(response.json()) > 0
    assert response.status_code == 200


def test_get_gocams_by_geneproduct_id_causal2():
    id = urllib.parse.quote("FB:FBgn0003731")
    data = {
        "causalmf": 2,
    }
    response = test_client.get(f"/api/gp/{id}/models", params=data)
    assert len(response.json()) > 0
    assert response.status_code == 200
