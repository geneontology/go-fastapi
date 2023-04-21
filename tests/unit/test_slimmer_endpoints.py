import logging

import pytest
from fastapi.testclient import TestClient
from pprint import pprint
from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192", "MGI:MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("endpoint", ["/api/bioentityset/slimmer/function"])
def test_slimmer_endpoint_fgf8a(endpoint):
    data = {
        "subject": "ZFIN:ZDB-GENE-980526-388",
        "slim": ["GO:0003674", "GO:0008150", "GO:0005575"],
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    assert len(response.json()) > 2
    pprint(response.json())
    for item in response.json():
        assert item.get("slim") in ["GO:0003674", "GO:0008150", "GO:0005575"]
        assert item.get("subject") == "ZFIN:ZDB-GENE-980526-388"
        assert item.get("assocs")
        for assoc in item.get("assocs"):
            assert assoc.get("evidence")


@pytest.mark.parametrize("endpoint", ["/api/bioentityset/slimmer/function"])
def test_slimmer_endpoint_shha(endpoint):
    data = {
        "subject": "ZFIN:ZDB-GENE-980526-166",
        "slim": ["GO:0005102"],
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    for item in response.json():
        assert item.get("slim") == "GO:0005102"
        assert item.get("subject") == "ZFIN:ZDB-GENE-980526-166"
        assert item.get("assocs")
        for assoc in item.get("assocs"):
            assert assoc.get("evidence")
    assert len(response.json()) > 0


@pytest.mark.parametrize("endpoint", ["/api/bioentityset/slimmer/function"])
def test_slimmer_endpoint_mgimgi(endpoint):
    data = {
        "subject": ["ZFIN:ZDB-GENE-980526-166", "MGI:3588192", "MGI:MGI:3588192"],
        "slim": ["GO:0005102"],
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    print (response.json())
    assert len(response.json()) > 0