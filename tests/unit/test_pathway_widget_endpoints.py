import logging
import urllib.parse
import unittest
import pytest
from fastapi.testclient import TestClient
from app.main import app

test_client = TestClient(app)
gene_ids = ["WB:WBGene00002147", "MGI:3588192", "FB:FBgn0003731"]
logger = logging.getLogger(__name__)


class TestGeneProductAPI(unittest.TestCase):

    @pytest.mark.parametrize("id", gene_ids)
    def test_get_gocams_by_geneproduct_id(self, id):
        """
        Test getting Gene Ontology models associated with a gene product by its ID.

        :param id: The identifier of the gene product. (parametrized)
        """
        response = test_client.get(f"/api/gp/{id}/models")
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


if __name__ == '__main__':
    unittest.main()
