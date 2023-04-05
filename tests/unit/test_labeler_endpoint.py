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


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontol/labeler",
    ],
)
def test_labeler_endpoint(endpoint):
    data = {"id": "GO:0003677"}
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    map_response = response.json()
    assert map_response["GO:0003677"] == "DNA binding"