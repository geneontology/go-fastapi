"""Unit tests for the endpoints in the pathway module."""
import logging
import unittest
import urllib.parse

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)
gene_ids = ["WB:WBGene00002147", "MGI:3588192", "FB:FBgn0003731"]
logging.basicConfig(filename='combined_access_error.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s')
logger = logging.getLogger()


class TestGeneProductAPI(unittest.TestCase):

    """Test the pathway API endpoints."""

    def test_get_gocams_by_geneproduct_id(self):
        """
        Test getting Gene Ontology models associated with a gene product by its ID.

        :param id: The identifier of the gene product. (parametrized)
        """
        for gene_id in gene_ids:
            response = test_client.get(f"/api/gp/{gene_id}/models")
            self.assertGreater(len(response.json()), 0)
            self.assertEqual(response.status_code, 200)

    def test_get_gocams_by_geneproduct_id_causal2(self):
        """
        Test getting Gene Ontology models associated with a gene product by its ID with causal2.

        This test uses causal2 parameter with a gene product identifier.

        :return: None
        """
        id = urllib.parse.quote("FB:FBgn0003731")
        data = {
            "causalmf": 2,
        }
        response = test_client.get(f"/api/gp/{id}/models", params=data)
        self.assertGreater(len(response.json()), 0)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
