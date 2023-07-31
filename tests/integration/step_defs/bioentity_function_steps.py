from pprint import pprint
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then
from app.main import app

EXTRA_TYPES = {
    "String": str,
}

@scenario("../features/bioentityfunction.feature", "test function endpoint")
def test_zfin():
    """
    Scenario: test function endpoint
    """
    # boilerplate
    pass

@scenario(
    "../features/bioentityfunction.feature",
    "User fetches all GO functional assignments for a human gene using an HGNC id",
)
def test_hgnc():
    """
    Scenario: User fetches all GO functional assignments for a human gene using an HGNC id
    """
    # boilerplate
    pass

@scenario(
    "../features/bioentityfunction.feature",
    "User fetches all GO functional assignments for a human gene using a NCBI ID",
)
def test_ncbi():
    """
    Scenario: User fetches all GO functional assignments for a human gene using a NCBI ID
    """
    # boilerplate
    pass

@scenario(
    "../features/bioentityfunction.feature",
    "User fetches GO functional assignments and wishes to filter negated results",
)
def test_negated():
    """
    Scenario: User fetches GO functional assignments and wishes to filter negated results
    """
    # boilerplate
    pass

# Given Steps

@given(
    parsers.cfparse(
        'the "{endpoint:String}" is queried with "{bioentity_id:String}"',
        extra_types=EXTRA_TYPES,
    ),
    target_fixture="result",
)
def api_result(bioentity_id):
    """
    Given the "{endpoint}" is queried with "{bioentity_id}".

    :param endpoint: The API endpoint to be queried.
    :type endpoint: str
    :param bioentity_id: The bioentity ID to be used in the query.
    :type bioentity_id: str
    :return: The response obtained after querying the API endpoint.
    :rtype: TestResponse
    """
    test_client = TestClient(app)
    response = test_client.get(f"/api/bioentity/gene/{bioentity_id}/function")
    return response

# Then Steps

@then(parsers.parse('the response status code is "{code:d}"'))
def response_code(result, code):
    """
    Then the response status code is {code}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param code: The expected status code.
    :type code: int
    """
    assert result.status_code == code

@then(
    parsers.cfparse(
        "the response contains an association with object.id of {term:String}",
        extra_types=EXTRA_TYPES,
    )
)
def endpoint_returns(result, term):
    """
    Then the response contains an association with object.id of {term}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param term: The expected term value to be present in the response.
    :type term: str
    """
    data = result.json()
    found_it = False
    term = term.replace('"', "")
    pprint(data)
    for association in data.get("associations"):
        if association.get("object").get("id") == term:
            found_it = True
    assert found_it

@then(
    parsers.cfparse(
        "the response should have an association with object.label of {name:String}",
        extra_types=EXTRA_TYPES,
    )
)
def endpoint_returns(result, name):
    """
    Then the response should have an association with object.label of {name}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param name: The expected name value to be present in the response.
    :type name: str
    """
    data = result.json()
    found_it = False
    for association in data.get("associations"):
        name = name.replace('"', "")
        if name == str(association.get("object").get("label")):
            found_it = True
    assert found_it

@then(
    parsers.cfparse(
        "the response should have an association with qualifiers of {qualifier:String}",
        extra_types=EXTRA_TYPES,
    )
)
def endpoint_retuns(result, qualifier):
    """
    Then the response should have an association with qualifiers of {qualifier}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param qualifier: The expected qualifier value to be present in the response.
    :type qualifier: str
    """
    data = result.json()
    found_it = False
    for association in data.get("associations"):
        qualifier = qualifier.replace('"', "")
        if "qualifier" in association:
            for item in association.get("qualifier"):
                if qualifier == item:
                    found_it = True
    assert found_it

@then(
    parsers.cfparse(
        "the response should have an association with associations.negated is {qualifier:String}",
        extra_types=EXTRA_TYPES,
    )
)
def endpoint_retuns(result, qualifier):
    """
    Then the response should have an association with associations.negated is {qualifier}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param qualifier: The expected qualifier value to be present in the response.
    :type qualifier: str
    """
    data = result.json()
    found_it = False
    for association in data.get("associations"):
        qualifier = qualifier.replace('"', "")
        if "negated" in association:
            negated = association.get("negated")
            if negated:
                found_it = True
    assert found_it