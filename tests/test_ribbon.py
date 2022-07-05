from fastapi.testclient import TestClient
from app.main import app
from pprint import pprint
test_client = TestClient(app)


gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]


def test_zebrafish_ribbon():
    data = {
        "subset": "goslim_agr",
        "subject": ["ZFIN:ZDB-GENE-980526-166"]
    }
    response = test_client.get(f"/ontology/ribbon/", params=data)
    for subject in response.json().get('subjects'):
        assert subject.get('label') == 'shha'
        assert subject.get('taxon_label') == 'Danio rerio'
        assert(subject.get('groups').get('GO:0003674'))
        assert(subject.get('groups').get('GO:0003674').get('ALL').get('nb_annotations') >= 5)
        assert (subject.get('groups').get('GO:0008150').get('ALL').get('nb_annotations') >= 95)
        assert(subject.get('groups').get('GO:0030154').get('ALL').get('nb_annotations') >= 22)
        assert (subject.get('groups').get('GO:0005575').get('ALL').get('nb_annotations') >= 4)
    assert response.status_code == 200


def test_human_ribbon():
    data = {
        "subset": "goslim_agr",
        "subject": ["HGNC:10848"]
    }
    response = test_client.get(f"/ontology/ribbon/", params=data)
    for subject in response.json().get('subjects'):
        assert subject.get('label') == 'SHH'
        assert subject.get('taxon_label') == 'Homo sapiens'
        assert(subject.get('groups').get('GO:0003674'))
        assert (subject.get('groups').get('GO:0003674').get('ALL').get('nb_annotations') >= 19)
        assert (subject.get('groups').get('GO:0008150').get('ALL').get('nb_annotations') >= 165)
        assert (subject.get('groups').get('GO:0030154').get('ALL').get('nb_annotations') >= 38)
    assert response.status_code == 200


def test_sars_cov2_ribbon():
    data = {
        "subset": "goslim_agr",
        "subject": ["RefSeq:P0DTD3"]
    }
    response = test_client.get(f"/ontology/ribbon/", params=data)
    assert len(response.json().get('subjects')) == 0


def test_annotation_not_available():
    data = {
        "subset": "goslim_agr",
        "subject": ["SGD:S000002812"]
    }
    response = test_client.get(f"/ontology/ribbon/", params=data)

    for subject in response.json().get('subjects'):
        assert subject.get('groups').get('GO:0008219') is None
