import logging
import unittest
from pprint import pprint
from fastapi.testclient import TestClient
from app.main import app
from app.utils.settings import ESOLR, ESOLRDoc

test_client = TestClient(app)
logger = logging.getLogger(__name__)

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]
uris = ["http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"]


class TestSearchAPI(unittest.TestCase):

    def test_golr_solr(self):
        """
        Test the GOLR Solr configuration.

        :return: None
        """
        self.assertEqual(ESOLR.GOLR.value, "https://golr-aux.geneontology.io/solr/")
        self.assertEqual(ESOLRDoc.ONTOLOGY.value, "ontology_class")

    def test_search_entity_ssh(self):
        """
        Test the search entity autocomplete for 'ssh' category.

        :return: None
        """
        data = {"category": "gene"}
        response = test_client.get("/api/search/entity/autocomplete/ssh", params=data)
        self.assertEqual(response.status_code, 200)

    def test_autocomplete_shh(self):
        """
        Test the autocomplete for 'shh' category.

        :return: None
        """
        data = {"category": "gene"}
        response = test_client.get("/api/search/entity/autocomplete/shh", params=data)
        self.assertIn("id", response.json().get("docs")[0])
        self.assertEqual(response.status_code, 200)

    def test_autocomplete_biological(self):
        """
        Test the autocomplete for 'biological' category.

        :return: None
        """
        response = test_client.get("/api/search/entity/autocomplete/biological")
        self.assertIn("id", response.json().get("docs")[0])
        pprint(response.json())
        self.assertEqual(response.status_code, 200)

    def test_autocomplete_go(self):
        """
        Test the autocomplete for 'go' category.

        :return: None
        """
        response = test_client.get("/api/search/entity/autocomplete/go")
        self.assertIn("id", response.json().get("docs")[0])
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
