from fastapi.testclient import TestClient
from app.main import app
import pytest
from pprint import pprint

test_client = TestClient(app)


gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8"]
go_ids = ["GO:0008150", "GO:0008149"]


@pytest.mark.parametrize("id", gene_ids)
def test_bioenty_id_endpoints(id):
    response = test_client.get(f"/bioentity/{id}")
    assert response.status_code == 200
    pprint(response.json())


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_function_id_endpoints(id):
    response = test_client.get(f"/bioentity/function/{id}")
    assert response.status_code == 200
    assert len(response.json()) > 99


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_endpoints(id):
    response = test_client.get(f"/bioentity/gene/{id}/function")
    assert response.status_code == 200
    assert len(response.json()) >= 4


@pytest.mark.parametrize(
    "endpoint",
    [
        "/bioentity/function/{id}/genes",
        "/bioentity/function/{id}/taxons"

    ]
)
def test_bioenty_gene_function_endpoints(endpoint):
    data = {
        id: "GO:0008150"
    }
    response = test_client.get(endpoint, params=data)
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
    response = test_client.get(endpoint, params=data)
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


def test_prefixes_contract_endpoint():
    data = {
        "uri": "https://www.informatics.jax.org/accession/MGI:1"
    }
    response = test_client.get('/identifier/prefixes/contract/{uri}', params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/identifier/prefixes/expand/{id}",

    ]
)
def test_expander_endpoint(endpoint):
    data = {
        id: "MGI:1"
    }
    response = test_client.get(endpoint, params=data)
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
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    map_response = response.json()
    assert map_response['GO:0003677'] == 'DNA binding'



@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}",

    ]
)
def test_term_id_endpoint(endpoint):
    data = {
        "id": "GO:0003677"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}/subsets",

    ]
)
def test_term_subsets_endpoint(endpoint):
    data = {
        "id": "GO:0003677"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/subset/{id}",

    ]
)
def test_term_by_subset_endpoint(endpoint):
    data = {
        "id": "goslim_agr"
    }
    response = test_client.get(endpoint, params=data)
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
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/shared/{subject}/{object}",

    ]
)
def test_ontology_ancestors_shared_sub_obj(endpoint):
    data = {
        "subject": "GO:0006259",
        "object": "GO:0046483"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/subset/{id}",

    ]
)
def test_ontology_subset(endpoint):
    data = {
        "id": "GO:0003677"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}",

    ]
)
def test_ontology_term_id(endpoint):
    data = {
        "id": "GO:0046483"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}/subgraph",

    ]
)
def test_ontology_term_graph(endpoint):
    data = {
        "id": "GO:0046483"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}/graph",

    ]
)
def test_ontology_term_subgraph(endpoint):
    data = {
        "id": "GO:0046483",
        "graph_type": "topology_graph"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ontology/term/{id}/subsets",

    ]
)
def test_ontology_term_subsets(endpoint):
    data = {
        "id": "GO:0046483"
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/search/entity/{id}",

    ]
)
def test_search_entity(endpoint):
    data = {
        'term': 'ssh',
        'category': 'gene',
        'boost_fix': '0',
        'boost_q': '0',
        'taxon': 'NCBITaxon:7955',
        'highlight_class': 'gene',
        'id': 'ssh'
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/search/entity/autocomplete/biological",

    ]
)
def test_autocomplete(endpoint):
    response = test_client.get(endpoint)
    assert response.status_code == 200