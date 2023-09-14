"""Unit tests for the endpoints in the models module."""

import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

test_client = TestClient(app)
gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]


class TestApp(unittest.TestCase):

    """Test the models endpoints."""

    def test_gometadata_by_model_ids(self):
        """Test the endpoint to retrieve GO metadata by model IDs."""
        data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
        response = test_client.get("/api/models/go", params=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_geneproductmetadata_by_model_ids(self):
        """Test the endpoint to retrieve gene product metadata by model IDs."""
        data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
        response = test_client.get("/api/models/gp", params=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_pubmedmetadata_by_model_ids(self):
        """Test the endpoint to retrieve PubMed metadata by model IDs."""
        data = {"gocams": ["59a6110e00000067", "SYNGO_369"]}
        response = test_client.get("/api/models/pmid", params=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_bioenty_id_endpoints(self):
        """Test the bioentity endpoint for each given ID."""
        for id in gene_ids:
            response = test_client.get(f"/api/bioentity/{id}")
            self.assertEqual(response.status_code, 200)

    def test_gocam_by_model_ids(self):
        """Test the endpoint to retrieve GO-CAMs by model IDs."""
        response = test_client.get("/api/models/581e072c00000820")
        self.assertGreater(len(response.json()), 125)
        self.assertEqual(response.status_code, 200)

    def test_models_size_endpoint(self):
        """Test the endpoint to retrieve models with specified size."""
        data = {
            "start": "32",
            "size": "10",
        }
        response = test_client.get("/api/models", params=data)
        for record in response.json():
            self.assertIsInstance(record.get("orcids"), list)
        self.assertEqual(response.status_code, 200)

    def test_userlist(self):
        """Test the endpoint to retrieve the list of users."""
        response = test_client.get("/api/users")
        self.assertGreater(len(response.json()), 100)
        self.assertEqual(response.status_code, 200)

    def test_grouplist(self):
        """Test the endpoint to retrieve the list of groups."""
        response = test_client.get("/api/groups")

        print(response.json())
        self.assertGreater(len(response.json()), 15)
        self.assertEqual(response.status_code, 200)

    def test_groups_by_name(self):
        """Test the endpoint to retrieve groups by name."""
        response = test_client.get("/api/groups/MGI")
        self.assertGreater(len(response.json()), 10)
        self.assertEqual(response.status_code, 200)

    def test_get_modelid_by_pmid(self):
        """Test the endpoint to retrieve model IDs by PubMed ID."""
        response = test_client.get("/api/pmid/15314168/models")
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.status_code, 200)

    def test_get_go_term_detail_by_go_id(self):
        """Test the endpoint to retrieve GO term details by GO ID."""
        response = test_client.get("/api/go/GO_0008150")
        self.assertIn("goid", response.json())
        self.assertIn("label", response.json())
        self.assertEqual(response.json()["goid"], "http://purl.obolibrary.org/obo/GO_0008150")
        self.assertEqual(response.json()["label"], "biological_process")
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.status_code, 200)

    def test_get_gocam_models_by_go_id(self):
        """Test the endpoint to retrieve GO-CAM models by GO ID."""
        id = "GO:0008150"
        response = test_client.get(f"/api/go/{id}/models")
        self.assertGreater(len(response.json()), 100)
        self.assertEqual(response.status_code, 200)

    def test_get_term_details_by_taxon_id(self):
        """Test the endpoint to retrieve term details by taxon ID."""
        taxon_id = "NCBITaxon:9606"
        response = test_client.get(f"/api/taxon/{taxon_id}/models")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 20)

    def test_get_pmid_by_model_id(self):
        """Test the endpoint to retrieve PubMed IDs by model ID."""
        response = test_client.get("/api/models/pmid", params={"gocams": ["59a6110e00000067"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertIn("gocam", response.json()[0])
        self.assertIn("sources", response.json()[0])


if __name__ == "__main__":
    unittest.main()
