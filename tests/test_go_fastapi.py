from fastapi.testclient import TestClient
from app.main import app
import pytest

test_client = TestClient(app)

@pytest.mark.parametrize(
    "endpoint",
    [
        "/bioentity/function/id"
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
        "/bioentity/gene/ZFIN%3AZDB-GENE-980526-388/function",
        "/bioentity/function/GO%3A0044598/genes",
        "/bioentity/function/ZFIN%3AZDB-GENE-980526-388/taxons",

    ]
)
def test_bioenty_endpoints(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize(
    "endpoint",
    [
        "/bioentity/gene/ZFIN%3AZDB-GENE-980526-388/function",
        "/bioentity/function/GO%3A0044598/genes",
        "/bioentity/function/ZFIN%3AZDB-GENE-980526-388/taxons",

    ]
)
def test_bioenty_endpoints(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize(
    "endpoint",
    [
        "/bioentityset/slimmer/function"
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
        "/identifier/prefixes",

    ]
)
def test_prefixes_endpoint(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/identifier/prefixes/contract/http%3A%2F%2Fwww.informatics.jax.org%2Faccession%2FMGI%3A1",

    ]
)
def test_prefixes_contract_endpoint(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/identifier/prefixes/expand/MGI%3A1",

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
        "/ontol/labeler",

    ]
)
def test_labeler_endpoint(endpoint):
    data = {
        "id": "GO:0003677"
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
    map_response = response.json
    assert map_response['GO:0003677'] == 'DNA binding'


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/GO%3A0003677/subsets",

    ]
)
def test_term_subsets_endpoint(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/subset/goslim_agr",

    ]
)
def test_term_by_subset_endpoint(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200



@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/ribbon/",

    ]
)
def test_ribbon_endpoint(endpoint):
    data = {
        "subset": "goslim_agr",
        "subject": ["RGD:620474"]
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/shared/GO%3A0006259/GO%3A0046483",

    ]
)
def test_ontology_shared_sub_obj(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/subset/goslim_agr",

    ]
)
def test_ontology_subset(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/GO%3A0046483",

    ]
)
def test_ontology_term_id(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/GO%3A0046483/subgraph",

    ]
)
def test_ontology_term_graph(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/GO%3A0046483/graph",

    ]
)
def test_ontology_term_subgraph(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/GO%3A0046483/subsets",

    ]
)
def test_ontology_term_subsets(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/search/entity/ssh",

    ]
)
def test_ontology_term_subsets(endpoint):
    data = {
        'term': 'ssh',
        'category': 'gene',
        'boost_fix': '0',
        'boost_q': '0',
        'taxon': 'NCBITaxon:7955',
        'highlight_class': 'gene'
    }
    response = test_client.get(endpoint, json=data)
    assert response.status_code == 200
