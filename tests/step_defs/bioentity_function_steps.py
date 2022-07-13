import pytest
from pytest_bdd import scenarios, given, then, parsers, scenario
from app.main import app
from fastapi.testclient import TestClient
from pprint import pprint

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
    print(term)
    data = result.json()
    pprint(data)
