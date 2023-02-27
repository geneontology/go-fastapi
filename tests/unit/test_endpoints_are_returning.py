from pprint import pprint

import pytest
from fastapi.testclient import TestClient
from app.utils.settings import ESOLR, ESOLRDoc, get_golr_config
# from ontobio.golr.golr_query import ESOLR, ESOLRDoc
from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


def test_golr_solr():
    assert ESOLR.GOLR.value == 'http://golr-aux.geneontology.io/solr/'
    assert ESOLRDoc.ONTOLOGY.value == 'ontology_class'


@pytest.mark.parametrize("id", gene_ids)
def test_bioenty_id_endpoints(id):
    response = test_client.get(f"/api/bioentity/{id}")
    assert response.status_code == 200
    pprint(response.json())


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
    pprint(response.json())


@pytest.mark.parametrize("id", go_ids)
def test_bioenty_gene_function_endpoints(id):
    response = test_client.get(f"/api/bioentity/function/{id}/taxons")
    assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ["/api/bioentityset/slimmer/function"])
def test_slimmer_endpoint(endpoint):
    data = {
        "subject": "ZFIN:ZDB-GENE-980526-388",
        "slim": ["GO:0003674", "GO:0008150", "GO:0005575"],
    }
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200
    assert len(response.json()) > 2


def test_prefixes_endpoint():
    response = test_client.get(f"/api/identifier/prefixes")
    assert response.status_code == 200


# @pytest.mark.parametrize("uri", uris)
# def test_prefixes_contract_endpoint(uri):
#     response = test_client.get(f"/api/identifier/prefixes/contract/{uri}")
#     print(response.json())
#     assert response.status_code == 200


@pytest.mark.parametrize("id", gene_ids)
def test_expander_endpoint(id):
    response = test_client.get(f"/api/identifier/prefixes/expand/{id}")
    print(response.json())
    assert response.status_code == 200


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


@pytest.mark.parametrize("id", go_ids)
def test_term_id_endpoint(id):
    response = test_client.get(f"/api/ontology/term/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_term_subsets_endpoint(id):
    response = test_client.get(f"/api/ontology/term/{id}/subsets")
    assert response.status_code == 200


@pytest.mark.parametrize("id", subsets)
def test_term_by_subset_endpoint(id):
    response = test_client.get(f"/api/ontology/subset/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/ribbon/",
    ],
)
def test_ribbon_endpoint(endpoint):
    data = {"subset": "goslim_agr", "subject": ["RGD:620474"]}
    response = test_client.get(endpoint, params=data)
    pprint(response.json())
    assert response.status_code == 200


def test_ontology_ancestors_shared_sub_obj():
    subject = "GO:0006259"
    object = "GO:0046483"
    response = test_client.get(f"/api/ontology/shared/{subject}/{object}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", subsets)
def test_ontology_subset(id):
    response = test_client.get(f"/api/ontology/subset/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_id(id):
    response = test_client.get(f"/api/ontology/term/{id}")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_graph(id):
    response = test_client.get(f"/api/ontology/term/{id}/subgraph")
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_subgraph(id):
    data = {"graph_type": "topology_graph"}
    response = test_client.get(f"/api/ontology/term/{id}/graph", params=data)
    print(response.json())
    assert response.status_code == 200


@pytest.mark.parametrize("id", go_ids)
def test_ontology_term_subsets(id):
    response = test_client.get(f"/api/ontology/term/{id}/subsets")
    assert response.status_code == 200


@pytest.mark.skip(
    reason="currently this endpoint is disabled because we "
    "have no 'facet_pivot' attribute in GOlr"
)
def test_search_entity():
    data = {
        "term": "ssh",
        "category": "gene",
        "boost_fix": "0",
        "boost_q": "0",
        "taxon": "NCBITaxon:7955",
        "highlight_class": "gene",
        "id": "ssh",
    }
    response = test_client.get(f"/api/search/entity/ssh", params=data)
    assert response.status_code == 200


def test_autocomplete():
    response = test_client.get(f"/api/search/entity/autocomplete/biological")
    assert response.status_code == 200


def test_autocomplete_go():
    response = test_client.get(f"/api/search/entity/autocomplete/go")
    assert response.status_code == 200


def test_models_size_endpoint():
    data = {
        "start": "1",
        "size": "10",
    }
    response = test_client.get(f"/api/models", params=data)
    print(response.json())
    assert response.status_code == 200