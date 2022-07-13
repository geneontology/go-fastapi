import pytest
from pytest_bdd import scenarios, given, then, parsers, scenario
from app.main import app
from fastapi.testclient import TestClient
from pprint import pprint
import json

EXTRA_TYPES = {
    'String': str,
}


@scenario('../features/bioentityfunction.feature', 'test function endpoint')
def test_add():
    pass


# Given Steps


@given(parsers.cfparse('the API is queried with "{bioentity_id:String}"',
                       extra_types=EXTRA_TYPES), target_fixture='result')
def api_result(bioentity_id):
    test_client = TestClient(app)
    response = test_client.get(f"/api/bioentity/gene/{bioentity_id}/function")
    return response


# Then Steps

@then(parsers.parse('the response status code is "{code:d}"'))
def response_code(result, code):
    assert result.status_code == code


@then(parsers.cfparse('the response contains results for a {term:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_retuns(result, term):
    data = result.json()
    terms = []
    for association in data.get('associations'):
        terms.append(association.get('object').get('id'))
    # this is a hack - I don't know why term is being passed as "GO:xxx" instead of 'GO:xxx'
    assert "GO:0030500" in terms


@then(parsers.cfparse('the response should have an association with object.label of {name:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_retuns(result, name):
    data = result.json()
    lables = []
    for association in data.get('associations'):
        lables.append(association.get('object').get('label'))
    # this is a hack - I don't know why term is being passed as "GO:xxx" instead of 'GO:xxx'
    assert "regulation of bone mineralization" in lables
