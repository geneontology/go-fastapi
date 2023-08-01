"""Prefix steps."""

from pprint import pprint

from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then

from app.main import app

EXTRA_TYPES = {
    "String": str,
}


@scenario("../features/prefixes.feature", "Client code requires list of all prefixes in use")
def test_identifiers():
    """Scenario: Client code requires list of all prefixes in use."""
    # boilerplate
    pass


@scenario("../features/prefixes.feature", "Expand a GO ID to a URI")
def test_exand_uri():
    """Scenario: Expand a GO ID to a URI."""
    # boilerplate
    pass


@given(
    parsers.cfparse("the {endpoint:String} is queried", extra_types=EXTRA_TYPES),
    target_fixture="result",
)
def api_result_first(endpoint):
    """
    Given the {endpoint} is queried.

    :param endpoint: The API endpoint to be queried.
    :type endpoint: str
    :return: The response obtained after querying the API endpoint.
    :rtype: TestResponse
    """
    test_client = TestClient(app)
    response = test_client.get("/api/identifier/prefixes")
    return response


@given(
    parsers.cfparse(
        'the "{endpoint:String}" endpoint is queried with "{thing:String}"',
        extra_types=EXTRA_TYPES,
    ),
    target_fixture="result",
)
def api_result_second(endpoint, thing):
    """
    Given the "{endpoint}" endpoint is queried with "{thing}".

    :param endpoint: The API endpoint to be queried.
    :type endpoint: str
    :param thing: The thing to be used in the query.
    :type thing: str
    :return: The response obtained after querying the API endpoint.
    :rtype: TestResponse
    """
    test_client = TestClient(app)
    print("")
    print(endpoint + thing)
    response = test_client.get(f"{endpoint}{thing}")
    pprint(response.json())
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


@then(parsers.cfparse('the content should contain "{content:String}"', extra_types=EXTRA_TYPES))
def contains(result, content):
    """
    Then the content should contain {content}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param content: The expected content to be present in the response.
    :type content: str
    """
    content = content.replace('"', "")
    assert content in result.json()
