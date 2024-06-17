"""Unit tests for the endpoints in the ribbon module."""
import unittest
from pprint import pprint

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "ZFIN:ZDB-GENE-990415-72"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]

uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


class TestOntologyAPI(unittest.TestCase):

    """Test the ribbon API endpoints."""

    def test_ribbon_endpoint(self):
        """
        Test the endpoint to get the ontology ribbon.

        :return: None
        """
        data = {"subset": "goslim_agr", "subject": ["RGD:620474"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertEqual(response.status_code, 200)

    def test_zebrafish_ribbon(self):
        """
        Test the ontology ribbon for zebrafish.

        :return: None
        """
        data = {"subset": "goslim_agr", "subject": ["ZFIN:ZDB-GENE-980526-166"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertEqual(subject.get("label"), "shha")
            self.assertEqual(subject.get("taxon_label"), "Danio rerio")
            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertGreaterEqual(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations"), 5)
            self.assertGreaterEqual(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations"), 93)
            self.assertGreaterEqual(subject.get("groups").get("GO:0030154").get("ALL").get("nb_annotations"), 22)
            self.assertGreaterEqual(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations"), 4)
        self.assertEqual(response.status_code, 200)

    # Add other test cases following a similar pattern

    def test_human_ribbon(self):
        """Test the ontology ribbon for human."""
        data = {"subset": "goslim_agr", "subject": ["HGNC:10848"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "SHH")
            self.assertTrue(subject.get("taxon_label") == "Homo sapiens")
            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 165)
            self.assertTrue(subject.get("groups").get("GO:0030154").get("ALL").get("nb_annotations") >= 38)
        self.assertTrue(response.status_code == 200)

    def test_sars_cov2_ribbon(self):
        """Test sars_cov2_ribbon."""
        data = {"subset": "goslim_agr", "subject": ["RefSeq:P0DTD3"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertTrue(len(response.json().get("subjects")) == 0)

    def test_sgd_ribbon_term(self):
        """Test sgd ribbon with not available annotations."""
        data = {"subset": "goslim_agr", "subject": ["SGD:S000002812"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        pprint(response.json())
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("groups").get("GO:0008219") is None)
            self.assertTrue(subject.get("groups").get("GO:0032991").get("ALL").get("nb_annotations") >= 5)
            self.assertTrue(subject.get("groups").get("GO:0032991").get("ALL").get("nb_classes") >= 2)
            self.assertTrue(subject.get("groups").get("GO:0032991").get("IDA").get("nb_annotations") >= 3)
            self.assertTrue(subject.get("groups").get("GO:0032991").get("IEA").get("nb_annotations") >= 1)
            self.assertTrue(subject.get("groups").get("GO:0032991").get("IBA").get("nb_annotations") >= 1)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("ALL").get("nb_annotations") >= 10)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("ALL").get("nb_classes") >= 7)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IGI").get("nb_annotations") >= 2)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IGI").get("nb_classes") >= 2)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IMP").get("nb_annotations") >= 1)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IMP").get("nb_classes") >= 1)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IEA").get("nb_annotations") >= 3)
            self.assertTrue(subject.get("groups").get("GO:0016070").get("IEA").get("nb_classes") >= 3)
            self.assertTrue(len(subject.get("groups")) == 14)
            self.assertTrue(subject.get("nb_classes") >= 19)
            self.assertTrue(subject.get("nb_annotations") >= 37)
        self.assertTrue(len(response.json().get("subjects")) == 1)

    def test_fly_ribbon(self):
        """Test fly ribbon returns."""
        data = {"subset": "goslim_agr", "subject": ["FB:FBgn0051155"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        pprint(response.json())
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "Polr2G")
            self.assertTrue(subject.get("taxon_label") == "Drosophila melanogaster")
            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 4)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 5)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 5)
        self.assertTrue(response.status_code == 200)

    def test_mgi_ribbon(self):
        """Test MGI ribbon annotation returns."""
        data = {"subset": "goslim_agr", "subject": ["MGI:1917258"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        pprint(response.json())
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "Ace2")
            self.assertTrue(subject.get("taxon_label") == "Mus musculus")
            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 14)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 16)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 14)
        self.assertTrue(response.status_code == 200)

    def test_wb_ribbon(self):
        """Test WB ribbon annotations."""
        data = {"subset": "goslim_agr", "subject": ["WB:WBGene00000898"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "daf-2")
            self.assertTrue(subject.get("taxon_label") == "Caenorhabditis elegans")
            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 19)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 70)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 71)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 10)
        assert response.status_code == 200

    def test_rgd_ribbon(self):
        """Test RGD annotations in the ribbon."""
        data = {"subset": "goslim_agr", "subject": ["RGD:70971"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        pprint(response.json())
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "Hamp")
            self.assertTrue(subject.get("taxon_label") == "Rattus norvegicus")

            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 5)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 50)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_classes") >= 39)
            self.assertTrue(subject.get("groups").get("GO:0005576").get("ALL").get("nb_classes") >= 2)
            self.assertTrue(subject.get("groups").get("GO:0005576").get("ALL").get("nb_annotations") >= 7)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 10)
        self.assertTrue(response.status_code == 200)

    def test_term_subsets_endpoint(self):
        """Test the endpoint to get the subsets of a Gene Ontology term by its identifier."""
        for id in go_ids:
            response = test_client.get(f"/api/ontology/term/{id}/subsets")
            self.assertEqual(response.status_code, 200)

    def test_term_by_subset_endpoint(self):
        """Test the endpoint to get the Gene Ontology terms associated with a given subset."""
        for id in subsets:
            response = test_client.get(f"/api/ontology/subset/{id}")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
