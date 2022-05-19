from fastapi.testclient import TestClient
from app.main import app
import pytest

test_client = TestClient(app)

@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/bioentity/function/id"
    ]
)
def test_bioenty_endpoints(endpoint):
    data = {
        'id': 'GO:0044598',
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
    assert len(response.json()) > 99


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/bioentity/gene/ZFIN%3AZDB-GENE-980526-388/function",
        "/api/bioentity/ZFIN%3AZDB-GENE-980526-388/associations",
        "/api/bioentity/function/ZFIN%3AZDB-GENE-980526-388/genes",
        "/api/bioentity/function/ZFIN%3AZDB-GENE-980526-388/taxons",

    ]
)
def test_bioenty_endpoints(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert len(response.json()) > 5


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/bioentity/gene/ZFIN%3AZDB-GENE-980526-388/function",
        "/api/bioentity/ZFIN%3AZDB-GENE-980526-388/associations",
        "/api/bioentity/function/ZFIN%3AZDB-GENE-980526-388/genes",
        "/api/bioentity/function/ZFIN%3AZDB-GENE-980526-388/taxons",

    ]
)
def test_bioenty_endpoints(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert len(response.json()) > 5


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/bioentityset/slimmer/function"
    ]
)
def test_slimmer_endpoint(endpoint):
    data = {
        'subject': 'ZFIN:ZDB-GENE-980526-388',
        'slim': ['GO:0003674', 'GO:0008150', 'GO:0005575']
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
    assert len(response.json()) > 2


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/identifier/prefixes",

    ]
)
def test_prefixes_endpoint(endpoint):
    data = {
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
    assert len(response.json()) > 2


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/identifier/prefixes/contract/http%3A%2F%2Fwww.informatics.jax.org%2Faccession%2FMGI%3A1",

    ]
)
def test_prefixes_contract_endpoint(endpoint):
    data = {
        "uri": "http://www.informatics.jax.org/accession/MGI:1"
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/identifier/prefixes/expand/MGI%3A1",

    ]
)
def test_expander_endpoint(endpoint):
    data = {
        "id": "MGI:1"
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontol/labeler/",

    ]
)
def test_labeler_endpoint(endpoint):
    data = {
        "id": "GO:0003677"
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
    map_response = response.json()
    assert map_response['GO:0003677'] == 'DNA binding'


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/ribbon/",

    ]
)
def test_ribbon_endpoint(endpoint):
    data = {
        "subset": "goslim_agr",
        "subject": "RGD:620474"
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/shared/GO%3A0006259/GO%3A0046483",

    ]
)
def test_ontology_shared_sub_obj(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/subset/goslim_agr",

    ]
)
def test_ontology_subset(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/term/GO%3A0046483",

    ]
)
def test_ontology_term_id(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/term/GO%3A0046483/subgraph",

    ]
)
def test_ontology_term_graph(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/term/GO%3A0046483/graph",

    ]
)
def test_ontology_term_subgraph(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/term/GO%3A0046483/subsets",

    ]
)
def test_ontology_term_subsets(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/search/entity/ssh",

    ]
)
def test_ontology_term_subsets(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200
