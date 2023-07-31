"""Unit tests for the endpoints in the ribbon module."""
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)
logger = logging.getLogger(__name__)

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


if __name__ == "__main__":
    unittest.main()
