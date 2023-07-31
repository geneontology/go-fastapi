"""Unit tests for the endpoints in the labeler module."""
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


class TestLabelerEndpoint(unittest.TestCase):

    """Test the labeler endpoint."""

    def test_labeler_endpoint(self):
        """
        Test the labeler endpoint with "GO:0003677".

        :return: None
        """
        endpoint = "/api/ontol/labeler"
        data = {"id": "GO:0003677"}
        response = test_client.get(endpoint, params=data)
        self.assertEqual(response.status_code, 200)
        map_response = response.json()
        self.assertEqual(map_response["GO:0003677"], "DNA binding")


if __name__ == "__main__":
    unittest.main()
