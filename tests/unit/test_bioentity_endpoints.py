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


def test_golr_solr():
    assert ESOLR.GOLR.value == "http://golr-aux.geneontology.io/solr/"
    assert ESOLRDoc.ONTOLOGY.value == "ontology_class"


@pytest.mark.parametrize("id", gene_ids)
def test_bioenty_id_endpoints(id):
    response = test_client.get(f"/api/bioentity/{id}")
    assert response.status_code == 200


def test_bioenty_id_endpoints_MGI():
    response = test_client.get("/api/bioentity/MGI:3588192")
    for item in response.json():
        assert item.get("id") == "MGI:3588192"
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_function_id_endpoints(id):
    response = test_client.get(f"/api/bioentity/function/{id}")
    assert response.status_code == 200
    assert len(response.json()) > 99


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_endpoints(id):
    response = test_client.get(f"/api/bioentity/gene/{id}/function")
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_function_endpoints(id):
    response = test_client.get(f"/api/bioentity/function/{id}/genes")
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_function_endpoints(id):
    response = test_client.get(f"/api/bioentity/function/{id}/genes")
    assert response.status_code == 200
    assert len(response.json()) >= 4


example = ["GO:0002544"]


@pytest.mark.parametrize("id", example)
def test_bioenty_gene_function_taxon_endpoint(id):
    data = {"taxon": "NCBITaxon:9606"}
    response = test_client.get(f"/api/bioentity/function/{id}/genes", params=data)
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_function_endpoints(id):
    response = test_client.get(f"/api/bioentity/function/{id}/taxons")
    assert response.status_code == 200
