import logging
import urllib.parse
from pprint import pprint

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.settings import ESOLR, ESOLRDoc, get_golr_config

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


def test_gometadata_by_model_ids():
    data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
    response = test_client.get("/api/models/go", params=data)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_geneproductmetadata_by_model_ids():
    data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
    response = test_client.get("/api/models/gp", params=data)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_pubmedmetadata_by_model_ids():
    data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
    response = test_client.get("/api/models/pmid", params=data)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.parametrize("id", gene_ids)
def test_bioenty_id_endpoints(id):
    response = test_client.get(f"/api/bioentity/{id}")
    assert response.status_code == 200


def test_gocam_by_model_ids():
    response = test_client.get("/api/models/581e072c00000820")
    assert len(response.json()) > 125
    assert response.status_code == 200


def test_models_size_endpoint():
    data = {
        "start": "32",
        "size": "10",
    }
    response = test_client.get(f"/api/models", params=data)
    for record in response.json():
        assert type(record.get("orcids")) == list
    assert response.status_code == 200


def test_userlist():
    response = test_client.get("/api/users")
    assert len(response.json()) > 100
    assert response.status_code == 200


def test_grouplist():
    response = test_client.get("/api/groups")
    assert len(response.json()) > 15
    assert response.status_code == 200


def test_groups_by_name():
    response = test_client.get("/api/groups/MGI")
    assert len(response.json()) > 10
    assert response.status_code == 200


def test_get_modelid_by_pmid():
    response = test_client.get("/api/pmid/15314168/models")
    assert len(response.json()) == 1
    assert response.status_code == 200


def test_get_go_term_detail_by_go_id():
    response = test_client.get("/api/go/GO_0008150")
    assert "goid" in response.json()
    assert "label" in response.json()
    assert response.json().get("goid") == "http://purl.obolibrary.org/obo/GO_0008150"
    assert response.json().get("label") == "biological_process"
    assert type(response.json()) == dict
    assert response.status_code == 200


def test_get_go_hierarchy_go_id():
    response = test_client.get("/api/go/GO_0008150/hierarchy")
    assert len(response.json()) >= 27791
    assert response.status_code == 200


def test_get_gocam_models_by_go_id():
    response = test_client.get("/api/go/GO_0008150/models")
    assert len(response.json()) >= 12979
    assert response.status_code == 200
