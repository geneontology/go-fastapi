from fastapi.testclient import TestClient
from app.main import app
import app.utils.ontology.ontology_utils as ou
from ontobio.sparql.sparql_ontology import EagerRemoteSparqlOntology
from pprint import pprint

test_client = TestClient(app)


def test_get_ontology():
    return_value = ou.get_ontology(id="go")
    assert type(return_value) is EagerRemoteSparqlOntology
    assert return_value.handle == "go"


def test_get_category_terms():
    assert False


def test_get_ontology_subsets_by_id():
    assert False


def test_correct_goid():
    assert False


def test_get_go_subsets():
    assert False


def test_go_summary():
    assert False
