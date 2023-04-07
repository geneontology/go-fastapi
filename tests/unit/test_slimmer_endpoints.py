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


@pytest.mark.parametrize("endpoint", ["/api/bioentityset/slimmer/function"])
def test_slimmer_endpoint(endpoint):
    data = {
        "subject": "ZFIN:ZDB-GENE-980526-388",
        "slim": ["GO:0003674", "GO:0008150", "GO:0005575"],
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    assert len(response.json()) > 2
