"""Unit tests for the endpoints in the models module."""

import logging
import unittest
from unittest import skip

from fastapi.testclient import TestClient
from requests import HTTPError

from app.main import app
from tests.integration.step_defs.bioentity_function_steps import response_code

logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

test_client = TestClient(app)
gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_cam_ids = ["gomodel:66187e4700001573", "66187e4700001573", "59a6110e00000067", "SYNGO_369",
              "581e072c00000820", "gomodel:59a6110e00000067", "gomodel:SYNGO_369"]
go_cam_not_found_ids = ["NGO_369", "581e072c000008", "gomodel:59a6110e000000",]

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

    def test_data_not_found_handling(self):
        """Test the endpoint to retrieve gene product metadata by model IDs."""
        data = {"gocams": ["gomodel:fake_id", "fake_id"]}
        response = test_client.get("/api/models/gp", params=data)
        print(response.json())
        self.assertEqual(response.status_code, 404)

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
        self.assertGreaterEqual(len(response.json()), 59)
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

        logger.info(response.json())
        self.assertGreater(len(response.json()), 15)
        self.assertEqual(response.status_code, 200)

    @skip("This test is skipped because it takes too long to run for GH actions.")
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
        response = test_client.get("/api/go/GO:0008150")
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
        self.assertGreater(len(response.json()), 800)

    def test_get_term_details_by_pombase_taxon_id(self):
        """Test the endpoint to retrieve term details by pombase taxon ID."""
        taxon_id = "NCBITaxon:4896"
        response = test_client.get(f"/api/taxon/{taxon_id}/models")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 10)

    def test_get_pmid_by_model_id(self):
        """Test the endpoint to retrieve PubMed IDs by model ID."""
        response = test_client.get("/api/models/pmid", params={"gocams": ["59a6110e00000067"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertIn("gocam", response.json()[0])
        self.assertIn("sources", response.json()[0])

    def test_get_model_details_by_model_id_json(self):
        """
        Test the endpoint to retrieve model details by model ID in JSON format from the S3 bucket, check for success.

        :return: None
        """
        for id in go_cam_ids:
            response = test_client.get(f"/api/go-cam/{id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get("id"), "gomodel:" + id.replace("gomodel:", ""))
            self.assertGreater(len(response.json().get("individuals")), 0)
            self.assertGreater(len(response.json().get("facts")), 0)

    def test_get_model_details_by_model_id_json_gocam_py(self):
        """
        Test the endpoint to retrieve model details by model ID in JSON format from the S3 bucket, check for success.

        :return: None
        """
        for id in go_cam_ids:
            response = test_client.get(f"/api/gocam-model/{id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get("id"), "gomodel:" + id.replace("gomodel:", ""))

    def test_get_model_details_by_model_id_json_gocam_py_failure(self):
        """
        Test the endpoint to retrieve model details by model ID in JSON format from the S3 bucket, check for 404 failures.

        :return: None
        """
        # Test with a non-existent model ID
        response = test_client.get("/api/gocam-model/67c10cc400005826")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "GO-CAM model not found.")

        # Test with other invalid ID formats
        invalid_ids = ["invalid-id", "12345", "not_a_valid_id"]
        for invalid_id in invalid_ids:
            response = test_client.get(f"/api/gocam-model/{invalid_id}")
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json().get("detail"), "GO-CAM model not found.")

    def test_get_model_details_by_model_id_not_found_json(self):
        """
        Test the endpoint to retrieve model details by model ID in JSON format from the S3 bucket, check for success.

        :return: None
        """
        for id in go_cam_not_found_ids:
            response = test_client.get(f"/api/go-cam/{id}")
            self.assertEqual(response.status_code, 404)

    def test_get_model_details_by_model_id_json_failure(self):
        """
        Test the endpoint to retrieve model details by model ID that does not exist, check for failure.

        :return: None
        """

        response = test_client.get("/api/go-cam/notatallrelevant")
        assert response.status_code == 404

    def test_get_model_details_by_model_id_json_failure_id(self):
        """
        Test the endpoint to retrieve model details by model ID that does not exist, check for failure.

        :return: None
        """
        response = test_client.get("/api/go-cam/gocam:59a6110e00000067")
        assert response.status_code == 404

if __name__ == "__main__":
    unittest.main()
