"""Unit tests for the endpoints in the slimmer module."""
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192", "MGI:MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


class TestSlimmerEndpoint(unittest.TestCase):
    """test the slimmer endpoints."""

    @unittest.skip("Endpoint not available")  # To skip the test since the endpoint is not available
    def test_slimmer_endpoint_fgf8a(self):
        """
        Test the slimmer endpoint for FGF8A gene.

        :return: None
        """
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": "ZFIN:ZDB-GENE-980526-388",
            "slim": ["GO:0003674", "GO:0008150", "GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 2)
        logger.info(response.json())
        for item in response.json():
            self.assertIn(item.get("slim"), ["GO:0003674", "GO:0008150", "GO:0005575"])
            self.assertEqual(item.get("subject"), "ZFIN:ZDB-GENE-980526-388")
            self.assertTrue(item.get("assocs"))
            for assoc in item.get("assocs"):
                self.assertTrue(assoc.get("evidence"))

    @unittest.skip("Endpoint not available")  # To skip the test since the endpoint is not available
    def test_slimmer_endpoint_shha(self):
        """
        Test the slimmer endpoint for SHHA gene.

        :return: None
        """
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": "ZFIN:ZDB-GENE-980526-166",
            "slim": ["GO:0005102"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        for item in response.json():
            self.assertEqual(item.get("slim"), "GO:0005102")
            self.assertEqual(item.get("subject"), "ZFIN:ZDB-GENE-980526-166")
            self.assertTrue(item.get("assocs"))
            for assoc in item.get("assocs"):
                self.assertTrue(assoc.get("evidence"))
        self.assertGreater(len(response.json()), 0)

    @unittest.skip("Endpoint not available")  # To skip the test since the endpoint is not available
    def test_slimmer_endpoint_mgimgi(self):
        """
        Test the slimmer endpoint for MGI gene.

        :return: None
        """
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["MGI:MGI:3588192"],
            "slim": ["GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        for subject in response.json().get("subjects"):
            print(subject)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)

    @unittest.skip("Endpoint not available")  # To skip the test since the endpoint is not available
    def test_slimmer_endpoint_mgi(self):
        """
        Test the slimmer endpoint for MGI gene.

        :return: None
        """
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["MGI:3588192"],
            "slim": ["GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)


if __name__ == "__main__":
    unittest.main()
