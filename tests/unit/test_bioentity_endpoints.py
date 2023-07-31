import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.utils.settings import ESOLR, ESOLRDoc

test_client = TestClient(app)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]

logger = logging.getLogger(__name__)


class TestBioentityEndpoints(unittest.TestCase):
    def test_golr_solr(self):
        """
        Test ESOLR constants for GOLR and ONTOLOGY.

        :return: None
        """
        self.assertEqual(ESOLR.GOLR.value, "https://golr-aux.geneontology.io/solr/")
        self.assertEqual(ESOLRDoc.ONTOLOGY.value, "ontology_class")

    def test_bioenty_id_endpoints(self):
        """
        Test bioentity ID endpoints.

        :return: None
        """
        for gene_id in gene_ids:
            response = test_client.get(f"/api/bioentity/{gene_id}")
            self.assertEqual(response.status_code, 200)

    def test_bioenty_id_endpoints_MGI(self):
        """
        Test bioentity ID endpoint for MGI:3588192.

        :return: None
        """
        response = test_client.get("/api/bioentity/MGI:3588192")
        self.assertEqual(response.status_code, 200)
        for item in response.json():
            self.assertEqual(item.get("id"), "MGI:3588192")

    def test_bioenty_function_id_endpoints(self):
        """
        Test bioentity function ID endpoints.

        :return: None
        """
        for go_id in go_ids:
            response = test_client.get(f"/api/bioentity/function/{go_id}")
            self.assertEqual(response.status_code, 200)
            self.assertGreater(len(response.json()), 99)

    def test_bioenty_gene_endpoints(self):
        """
        Test bioentity gene endpoints.

        :return: None
        """
        for go_id in go_ids:
            response = test_client.get(f"/api/bioentity/gene/{go_id}/function")
            self.assertEqual(response.status_code, 200)
            self.assertGreaterEqual(len(response.json()), 4)

    def test_bioenty_gene_function_endpoints(self):
        """
        Test bioentity gene function endpoints.

        :return: None
        """
        for go_id in go_ids:
            response = test_client.get(f"/api/bioentity/function/{go_id}/genes")
            self.assertEqual(response.status_code, 200)
            self.assertGreaterEqual(len(response.json()), 4)

    def test_bioenty_gene_function_taxon_endpoint(self):
        """
        Test bioentity gene function taxon endpoint.

        :return: None
        """
        for go_id in go_ids:
            data = {"taxon": "NCBITaxon:9606"}
            response = test_client.get(f"/api/bioentity/function/{go_id}/genes", params=data)
            self.assertEqual(response.status_code, 200)
            self.assertGreaterEqual(len(response.json()), 4)

    def test_bioenty_gene_function_endpoints_taxons(self):
        """
        Test bioentity gene function endpoints taxons.

        :return: None
        """
        for go_id in go_ids:
            response = test_client.get(f"/api/bioentity/function/{go_id}/taxons")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
