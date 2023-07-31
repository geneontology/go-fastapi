import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "ZFIN:ZDB-GENE-990415-72"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]

logger = logging.getLogger(__name__)

uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/ontology/ribbon/",
    ],
)
def test_ribbon_endpoint(endpoint):
    data = {"subset": "goslim_agr", "subject": ["RGD:620474"]}
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 200


def test_zebrafish_ribbon():
    data = {"subset": "goslim_agr", "subject": ["ZFIN:ZDB-GENE-980526-166"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "shha"
        assert subject.get("taxon_label") == "Danio rerio"
        assert subject.get("groups").get("GO:0003674")
        assert (  # molecular function
            subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 5
        )
        assert (  # biological process
            subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 93
        )
        assert (  # cell differentiation
            subject.get("groups").get("GO:0030154").get("ALL").get("nb_annotations") >= 22
        )
        assert (  # cellular component
            subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 4
        )
    assert response.status_code == 200


def test_human_ribbon():
    data = {"subset": "goslim_agr", "subject": ["HGNC:10848"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "SHH"
        assert subject.get("taxon_label") == "Homo sapiens"
        assert subject.get("groups").get("GO:0003674")
        assert subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 19
        assert subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 165
        assert subject.get("groups").get("GO:0030154").get("ALL").get("nb_annotations") >= 38
    assert response.status_code == 200


def test_sars_cov2_ribbon():
    data = {"subset": "goslim_agr", "subject": ["RefSeq:P0DTD3"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    assert len(response.json().get("subjects")) == 0


def test_sgd_ribbon_term_not_available():
    data = {"subset": "goslim_agr", "subject": ["SGD:S000002812"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)

    for subject in response.json().get("subjects"):
        assert subject.get("groups").get("GO:0008219") is None


def test_fly_ribbon():
    data = {"subset": "goslim_agr", "subject": ["FB:FBgn0051155"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "Polr2G"
        assert subject.get("taxon_label") == "Drosophila melanogaster"
        assert subject.get("groups").get("GO:0003674")
        assert subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 4
        assert subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 5
        assert subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 5
    assert response.status_code == 200


def test_mgi_ribbon():
    data = {"subset": "goslim_agr", "subject": ["MGI:1917258"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "Ace2"
        assert subject.get("taxon_label") == "Mus musculus"
        assert subject.get("groups").get("GO:0003674")
        assert subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 14
        assert subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 16
        assert subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 14
    assert response.status_code == 200


def test_wb_ribbon():
    data = {"subset": "goslim_agr", "subject": ["WB:WBGene00000898"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "daf-2"
        assert subject.get("taxon_label") == "Caenorhabditis elegans"
        assert subject.get("groups").get("GO:0003674")
        assert subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 19
        assert subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 72
        assert subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 10
    assert response.status_code == 200


def test_rgd_ribbon():
    data = {"subset": "goslim_agr", "subject": ["RGD:70971"]}
    response = test_client.get("/api/ontology/ribbon/", params=data)
    for subject in response.json().get("subjects"):
        assert subject.get("label") == "Hamp"
        assert subject.get("taxon_label") == "Rattus norvegicus"
        assert subject.get("groups").get("GO:0003674")
        assert subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 5
        assert subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 45
        assert subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 9
    assert response.status_code == 200
