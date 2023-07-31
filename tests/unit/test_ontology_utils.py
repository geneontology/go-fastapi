import logging
import unittest
import pytest
from fastapi.testclient import TestClient
from ontobio.sparql.sparql_ontology import EagerRemoteSparqlOntology

import app.utils.ontology.ontology_utils as ou
from app.main import app
from app.utils.settings import get_golr_config

test_client = TestClient(app)
logger = logging.getLogger(__name__)
go_ids = ["GO:0008150"]


class TestOntologyUtils(unittest.TestCase):

    def test_get_ontology_config(self):
        """
        Test getting the ontology config from golr.
        """
        golr_url = get_golr_config()["solr_url"]["url"]
        self.assertIn("golr-aux.geneontology.io", golr_url)

    def test_go_sparql(self):
        """
        Test fetching label for a given GO term.
        """
        results = ou.goont_fetch_label("GO:0008150")
        self.assertEqual(results, "biological_process")

    def test_get_ontology(self):
        """
        Test getting the ontology by ID.
        """
        return_value = ou.get_ontology(id="go")
        self.assertIsInstance(return_value, EagerRemoteSparqlOntology)
        self.assertEqual(return_value.handle, "go")

    def test_get_category_terms(self):
        """
        Test getting terms of a category.
        """
        category = {
            # ... (omitted for brevity)
        }

        return_value = ou.get_category_terms(category)
        self.assertEqual(len(return_value), 16)
        terms = [term.get("id") for term in return_value]
        self.assertIn("GO:0005783", terms)

    def test_get_ontology_subsets_by_id(self):
        """
        Test getting subsets of an ontology by ID.
        """
        ribbon_categories = ou.get_ontology_subsets_by_id("goslim_agr")
        self.assertEqual(len(ribbon_categories), 3)
        for ribbon_category in ribbon_categories:
            if ribbon_category.get("annotation_class") == "GO:0003674":
                self.assertEqual(len(ribbon_category.get("terms")), 16)

    def test_correct_goid(self):
        """
        Test correcting a GO ID.
        """
        corrected_id = ou.correct_goid(goid="GO:00012345")
        self.assertEqual(corrected_id, "GO_00012345")

    def test_get_go_subsets(self):
        """
        Test getting GO subsets.
        """
        subset_sparql = ou.get_go_subsets_sparql_query(goid="GO:0003674")
        self.assertIsNotNone(subset_sparql)
        self.assertIn("GO_0003674", subset_sparql)

    def test_create_go_summary_sparql(self):
        """
        Test creating a GO summary sparql query.
        """
        go_summary_sparql = ou.create_go_summary_sparql(goid="GO:0003674")
        self.assertIsNotNone(go_summary_sparql)
        self.assertIn("GO_0003674", go_summary_sparql)

    @pytest.mark.parametrize("id", go_ids)
    def test_get_go_hierarchy_go_id(self, id):
        """
        Test getting GO hierarchy for a given GO ID.
        """
        response = test_client.get(f"/api/go/{id}/hierarchy")
        self.assertGreater(len(response.json()), 0)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
