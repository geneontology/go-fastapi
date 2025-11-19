"""Unit tests for the endpoints in the ribbon module."""
import unittest

from fastapi.testclient import TestClient

from app.main import app
import logging

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "ZFIN:ZDB-GENE-990415-72", 
             "HGNC:8725", "HGNC:8729"]
ortho_gene_ids = ["WB:WBGene00002147", "HGNC:3449", "HGNC:16942", "HGNC:8725", "HGNC:8729",
                  "MGI:1930134", "MGI:1349436", "RGD:1559716",
                  "RGD:1308743", "Xenbase:XB-GENE-4594134", "ZFIN:ZDB-GENE-050522-431",
                  "ZFIN:ZDB-GENE-090312-15", "FB:FBgn0261984", "SGD:S000001121"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]

uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger()

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
        logger.info(response.json())
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
        for subject in response.json().get("subjects"):
            print(subject.get("id"))
            self.assertFalse(subject.get("id").startswith("MGI:MGI:"))
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
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 17)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 65)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 10)
        assert response.status_code == 200

    def test_rgd_ribbon(self):
        """Test RGD annotations in the ribbon."""
        data = {"subset": "goslim_agr", "subject": ["RGD:70971"]}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        logger.info(response.json())
        self.assertTrue(len(response.json().get("subjects")) > 0)
        for subject in response.json().get("subjects"):
            self.assertTrue(subject.get("label") == "Hamp")
            self.assertTrue(subject.get("taxon_label") == "Rattus norvegicus")

            self.assertTrue(subject.get("groups").get("GO:0003674"))
            self.assertTrue(subject.get("groups").get("GO:0003674").get("ALL").get("nb_annotations") >= 5)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_annotations") >= 47)
            self.assertTrue(subject.get("groups").get("GO:0008150").get("ALL").get("nb_classes") >= 37)
            self.assertTrue(subject.get("groups").get("GO:0005576").get("ALL").get("nb_classes") >= 2)
            self.assertTrue(subject.get("groups").get("GO:0005576").get("ALL").get("nb_annotations") >= 7)
            self.assertTrue(subject.get("groups").get("GO:0005575").get("ALL").get("nb_annotations") >= 10)
        self.assertTrue(response.status_code == 200)


    def test_mgi_ortho_ribbon_calls(self):
        """Test MGI ortholog ribbon annotations."""
        data = {"subset": "goslim_agr", "subject": ["MGI:88469","Xenbase:XB-GENE-994160",
                                                    "HGNC:2227","RGD:2378",
                                                    "ZFIN:ZDB-GENE-060606-1","FB:FBgn003185"],
                 "exclude_PB":"true",
                 "exclude_IBA":"false",
                 "cross_aspect":"false"
                }
        response = test_client.get("/api/ontology/ribbon/", params=data)
        self.assertGreater(len(response.json().get("subjects")),  0)
        self.assertIn("MGI:88469", [subject.get("id") for subject in response.json().get("subjects")])
        self.assertEqual(response.status_code, 200)

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

    def test_ribbon_with_many_subjects(self):
        """Test the ontology ribbon with many subjects."""
        data = {"subset": "goslim_agr", "subject": ortho_gene_ids,
                "exclude_PB":True, "exclude_IBA":False, "cross_aspect":False}
        response = test_client.get("/api/ontology/ribbon/", params=data)
        data = response.json()
        for subject in data.get("subjects"):
            print(subject.get("id"))
            self.assertFalse(subject.get("id").startswith("MGI:MGI:"))
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
