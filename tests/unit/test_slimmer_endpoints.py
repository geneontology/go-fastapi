"""Unit tests for the endpoints in the slimmer module."""
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

gene_ids = [
    "ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", 
    "MGI:3588192", "MGI:MGI:3588192", "HGNC:8725", "HGNC:8729"
]
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

    def test_hgnc_8725_slimmer_function(self):
        """Test slimmer function endpoint returns results for HGNC:8725."""
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["HGNC:8725"],
            "slim": ["GO:0008150", "GO:0003674", "GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        self.assertGreater(len(response_data), 0)
        
        # Verify response structure and that we have results for our subject
        found_subject = False
        for item in response_data:
            self.assertIn("subject", item)
            self.assertIn("slim", item)
            self.assertIn("assocs", item)
            if item.get("subject") == "HGNC:8725":
                found_subject = True
                self.assertIn(item.get("slim"), ["GO:0008150", "GO:0003674", "GO:0005575"])
                self.assertIsInstance(item.get("assocs"), list)
                self.assertGreater(len(item.get("assocs", [])), 0, "HGNC:8725 should have annotations")
        
        self.assertTrue(found_subject, "Should find results for HGNC:8725")

    def test_hgnc_8729_slimmer_function(self):
        """Test slimmer function endpoint returns results for HGNC:8729."""
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["HGNC:8729"],
            "slim": ["GO:0008150", "GO:0003674", "GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        self.assertGreater(len(response_data), 0)
        
        # Verify response structure and that we have results for our subject
        found_subject = False
        for item in response_data:
            self.assertIn("subject", item)
            self.assertIn("slim", item)
            self.assertIn("assocs", item)
            if item.get("subject") == "HGNC:8729":
                found_subject = True
                self.assertIn(item.get("slim"), ["GO:0008150", "GO:0003674", "GO:0005575"])
                self.assertIsInstance(item.get("assocs"), list)
                self.assertGreater(len(item.get("assocs", [])), 0, "HGNC:8729 should have annotations")
        
        self.assertTrue(found_subject, "Should find results for HGNC:8729")

    def test_hgnc_8725_and_8729_slimmer_function(self):
        """Test slimmer function endpoint returns results for both HGNC:8725 and HGNC:8729."""
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["HGNC:8725", "HGNC:8729"],
            "slim": ["GO:0008150", "GO:0003674", "GO:0005575"],
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        self.assertGreater(len(response_data), 0)
        
        # Verify we get results for both subjects
        found_subjects = set()
        for item in response_data:
            self.assertIn("subject", item)
            self.assertIn("slim", item)
            self.assertIn("assocs", item)
            
            subject_id = item.get("subject")
            if subject_id in ["HGNC:8725", "HGNC:8729"]:
                found_subjects.add(subject_id)
                self.assertIn(item.get("slim"), ["GO:0008150", "GO:0003674", "GO:0005575"])
                self.assertIsInstance(item.get("assocs"), list)
                self.assertGreater(len(item.get("assocs", [])), 0, f"{subject_id} should have annotations")
        
        self.assertIn("HGNC:8725", found_subjects, "Should find results for HGNC:8725")
        self.assertIn("HGNC:8729", found_subjects, "Should find results for HGNC:8729")

    def test_hgnc_8725_slimmer_specific_slim(self):
        """Test slimmer function with HGNC:8725 and specific GO slim terms."""
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["HGNC:8725"],
            "slim": ["GO:0008150"],  # biological_process
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        
        # Check that we get specific results for the requested slim
        for item in response_data:
            if item.get("subject") == "HGNC:8725":
                self.assertEqual(item.get("slim"), "GO:0008150")
                self.assertIsInstance(item.get("assocs"), list)

    def test_hgnc_8729_slimmer_specific_slim(self):
        """Test slimmer function with HGNC:8729 and specific GO slim terms."""
        endpoint = "/api/bioentityset/slimmer/function"
        data = {
            "subject": ["HGNC:8729"],
            "slim": ["GO:0003674"],  # molecular_function
        }
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIsInstance(response_data, list)
        
        # Check that we get specific results for the requested slim
        for item in response_data:
            if item.get("subject") == "HGNC:8729":
                self.assertEqual(item.get("slim"), "GO:0003674")
                self.assertIsInstance(item.get("assocs"), list)


if __name__ == "__main__":
    unittest.main()
