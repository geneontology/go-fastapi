import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app

test_client = TestClient(app)
logger = logging.getLogger(__name__)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


def test_prefixes_endpoint():
    response = test_client.get(f"/api/identifier/prefixes")
    assert response.status_code == 200


@pytest.mark.parametrize("id", gene_ids)
def test_expander_endpoint(id):
    response = test_client.get(f"/api/identifier/prefixes/expand/{id}")
    assert response.status_code == 200