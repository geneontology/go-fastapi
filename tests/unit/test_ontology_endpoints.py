"""Unit tests for the endpoints in the ontology module."""
import unittest

from fastapi.testclient import TestClient

from app.main import app

test_client = TestClient(app)

# Test data
gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]
subgraphs = ["GO:0009453", "GO:0052128", "GO:0052131"]  # energy taxis, positive energy taxis, positive aerotaxis

class TestApp(unittest.TestCase):

    """Test the ontology endpoints."""

    def test_term_id_endpoint(self):
        """Test the endpoint to get the details of a Gene Ontology term by its identifier."""
        for id in go_ids:
            response = test_client.get(f"/api/ontology/term/{id}")
            self.assertEqual(response.status_code, 200)

    def test_ontology_ancestors_shared_sub_obj(self):
        """Test the endpoint to get shared ancestors between two Gene Ontology terms."""
        subject = "GO:0006259"
        object = "GO:0046483"
        response = test_client.get(f"/api/ontology/shared/{subject}/{object}")
        self.assertEqual(response.status_code, 200)

    def test_ontology_subset(self):
        """Test the endpoint to get the details of a Gene Ontology subset by its identifier."""
        for id in subsets:
            response = test_client.get(f"/api/ontology/subset/{id}")
            self.assertEqual(response.status_code, 200)

    def test_ontology_term_graph(self):
        """Test the endpoint to get the graph of a Gene Ontology term by its identifier."""
        data = {"graph_type": "topology_graph"}
        for id in go_ids:
            response = test_client.get(f"/api/ontology/term/{id}/graph", params=data)
            self.assertEqual(response.status_code, 200)

    def test_ontology_term_subgraph(self):
        """Test the endpoint to get the subgraph of a Gene Ontology term by its identifier."""
        for id in subgraphs:
            response = test_client.get(f"/api/ontology/term/{id}/subgraph")
            self.assertEqual(response.status_code, 200)
            if id == "GO:0009453":
                self.assertGreaterEqual(len(response.json()["ancestors"]), 6)
                self.assertGreaterEqual(len(response.json()["descendents"]), 11)


if __name__ == "__main__":
    unittest.main()
