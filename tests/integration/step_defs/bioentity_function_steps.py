from pytest_bdd import scenarios, given, then, parsers, scenario
from app.main import app
from fastapi.testclient import TestClient
from pprint import pprint

EXTRA_TYPES = {
    'String': str,
}


@scenario('../features/bioentityfunction.feature', 'test function endpoint')
def test_zfin():
    # boilerplate
    pass


@scenario("../features/bioentityfunction.feature", 'User fetches all GO functional assignments for a human gene '
                                                   'using an HGNC id')
def test_hgnc():
    # boilerplate
    pass


@scenario("../features/bioentityfunction.feature", 'User fetches all GO functional assignments for a '
                                                   'human gene using a NCBI ID')
def test_ncbi():
    # boilerplate
    pass


@scenario("../features/bioentityfunction.feature", 'User fetches GO functional assignments and '
                                                   'wishes to filter negated results')
def test_negated():
    # boilerplate
    pass


# Given Steps


@given(parsers.cfparse('the "{endpoint:String} is queried with "{bioentity_id:String}"',
                       extra_types=EXTRA_TYPES), target_fixture='result')
def api_result(bioentity_id):
    test_client = TestClient(app)
    response = test_client.get(f"/api/bioentity/gene/{bioentity_id}/function")
    return response


# Then Steps

@then(parsers.parse('the response status code is "{code:d}"'))
def response_code(result, code):
    assert result.status_code == code


@then(parsers.cfparse('the response contains an association with object.id of {term:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_returns(result, term):
    data = result.json()
    found_it = False
    term = term.replace('"', '')
    pprint(data)
    for association in data.get('associations'):
        if association.get('object').get('id') == term:
            found_it = True
    assert found_it


@then(parsers.cfparse('the response should have an association with object.label of {name:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_returns(result, name):
    data = result.json()
    found_it = False
    for association in data.get('associations'):
        name = name.replace('"', '')
        if name == str(association.get('object').get('label')):
            found_it = True
    assert found_it


@then(parsers.cfparse('the response should have an association with qualifiers of {qualifier:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_retuns(result, qualifier):
    data = result.json()
    found_it = False
    for association in data.get('associations'):
        qualifier = qualifier.replace('"', '')
        if "qualifier" in association:
            for item in association.get('qualifier'):
                if qualifier == item:
                    found_it = True
    assert found_it


@then(parsers.cfparse('the response should have an association with associations.negated is {qualifier:String}',
                      extra_types=EXTRA_TYPES))
def endpoint_retuns(result, qualifier):
    data = result.json()
    found_it = False
    for association in data.get('associations'):
        qualifier = qualifier.replace('"', '')
        if "negated" in association:
            negated = association.get('negated')
            if negated:
                found_it = True
    assert found_it
