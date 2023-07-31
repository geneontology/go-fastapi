"""Unit tests for the endpoints in the prefix module."""
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)
logger = logging.getLogger(__name__)

gene_ids = [
    "ZFIN:ZDB-GENE-980526-388",
    "ZFIN:ZDB-GENE-990415-8",
    "MGI:3588192",
    "MGI:MGI:3588192",
    "FB:FBgn0003731",
]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]


class TestIdentifierAPI(unittest.TestCase):
    def test_expander_endpoint(self):
        """Test expanding an identifier with a given prefix."""
        for gene_id in gene_ids:
            response = test_client.get(f"/api/identifier/prefixes/expand/{gene_id}")
            self.assertEqual(response.status_code, 200)

    def test_contract_uri(self):
        """
        Test contracting a URI to a compact identifier.

        :return: None
        """
        uri = "http://purl.obolibrary.org/obo/GO_0008150"
        response = test_client.get("/api/identifier/prefixes/contract/", params={"uri": uri})
        self.assertEqual(response.status_code, 200)
        self.assertIn("GO:0008150", response.json())

    def test_get_all_prefixes(self):
        """
        Test getting all available identifier prefixes.

        :return: None
        """
        response = test_client.get("/api/identifier/prefixes")
        self.assertGreater(len(response.json()), 50)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
