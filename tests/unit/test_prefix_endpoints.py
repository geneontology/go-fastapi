import logging
from pprint import pprint
import pytest
from fastapi.testclient import TestClient
import urllib
from app.main import app

test_client = TestClient(app)
logger = logging.getLogger(__name__)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192", "FB:FBgn0003731"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]


@pytest.mark.parametrize("id", gene_ids)
def test_expander_endpoint(id):
    response = test_client.get(f"/api/identifier/prefixes/expand/{id}")
    pprint(response.json())
    assert response.status_code == 200


def test_contract_uri():
    uri = "http://purl.obolibrary.org/obo/GO_0008150"
    response = test_client.get("/api/identifier/prefixes/contract/", params={"uri": uri})
    assert response.status_code == 200
    assert "GO:0008150" in response.json()


def test_get_all_prefixes():
    response = test_client.get(f"/api/identifier/prefixes")
    assert len(response.json()) > 380
    assert response.status_code == 200