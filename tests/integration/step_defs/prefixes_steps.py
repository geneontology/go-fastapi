from pytest_bdd import scenarios, given, then, parsers, scenario
from app.main import app
from fastapi.testclient import TestClient
from pprint import pprint

EXTRA_TYPES = {
    'String': str,
}


@scenario('../features/prefixes.feature', 'Client code requires list of all prefixes in use')
def test_identifiers():
    # boilerplate
    pass

#
# @scenario('../features/prefixes.feature', 'Contract a GO URI to a GO OBO-style ID')
# def test_go_obo_style_uri():
#     # boilerplate
#     pass
#
#


@scenario('../features/prefixes.feature', 'Expand a GO ID to a URI')
def test_exand_uri():
    # boilerplate
    pass


@given(parsers.cfparse('the {endpoint:String} is queried', extra_types=EXTRA_TYPES), target_fixture='result')
def api_result(endpoint):
    test_client = TestClient(app)
    response = test_client.get(f"/api/identifier/prefixes")
    return response


@given(parsers.cfparse('the "{endpoint:String}" endpoint is queried with "{thing:String}"',
                       extra_types=EXTRA_TYPES), target_fixture='result')
def api_result(endpoint, thing):
    test_client = TestClient(app)
    print("")
    print(endpoint+thing)
    response = test_client.get(f"{endpoint}{thing}")
    pprint(response.json())
    return response


# Then Steps

@then(parsers.parse('the response status code is "{code:d}"'))
def response_code(result, code):
    assert result.status_code == code


@then(parsers.cfparse('the content should contain "{content:String}"', extra_types=EXTRA_TYPES))
def contains(result, content):
    content = content.replace('"', "")
    assert content in result.json()
