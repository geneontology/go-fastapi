import logging
import urllib.parse
from pprint import pprint
from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "WB:WBGene00002147",
            "ZFIN:ZDB-GENE-990415-8", "MGI:3588192", "FB:FBgn0003731"]

logger = logging.getLogger(__name__)


def test_get_gocams_by_geneproduct_id():
    id = urllib.parse.quote("MGI:3588192")
    response = test_client.get(f"/api/gp/{id}/models")
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
