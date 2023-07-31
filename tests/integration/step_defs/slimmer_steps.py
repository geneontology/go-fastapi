"""
slimmer steps
"""
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then

from app.main import app

EXTRA_TYPES = {
    "String": str,
}


@scenario("../features/slimmer.feature", "slimmer routes work as expected")
def test_slim():
    """Scenario: slimmer routes work as expected."""
    pass


# Given Steps


@given(
    parsers.cfparse(
        'the "{endpoint:String} is queried with gene "{bioentity_id:String} and slim {slimterms:String}"',
        extra_types=EXTRA_TYPES,
    ),
    target_fixture="result",
)
def api_result(bioentity_id, slimterms):
    """
    Given the endpoint is queried with gene {bioentity_id} and slim {slimterms}.

    :param bioentity_id: The bioentity ID to be queried.
    :type bioentity_id: str
    :param slimterms: Comma-separated slim terms to be used for querying.
    :type slimterms: str

    :return: The response obtained after querying the API endpoint.
    :rtype: TestResponse
    """
    test_client = TestClient(app)
    slimterms = slimterms.replace('"', "")
    slimterms_list = slimterms.split(",")
    data = {"subject": bioentity_id.replace('"', ""), "slim": slimterms_list}
    response = test_client.get("/api/bioentityset/slimmer/function", params=data)
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
        "the response should have an association with subject.label of {bioentity_label:String}",
        extra_types=EXTRA_TYPES,
    )
)
def subject_label(result, bioentity_label):
    """
    Then the response should have an association with subject.label of {bioentity_label}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param bioentity_label: The expected bioentity label.
    :type bioentity_label: str
    """
    data = result.json()
    found_it = False
    bioentity_label = bioentity_label.replace('"', "")
    bioentity_label = bioentity_label.strip()
    for item in data:
        for association in item.get("assocs"):
            if association.get("subject").get("label") == bioentity_label:
                found_it = True
    assert found_it


@then(
    parsers.cfparse(
        "the response contains an association with subject.id of {bioentity_id:String}",
        extra_types=EXTRA_TYPES,
    )
)
def subject_id(result, bioentity_id):
    """
    Then the response contains an association with subject.id of {bioentity_id}.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param bioentity_id: The expected bioentity ID.
    :type bioentity_id: str
    """
    data = result.json()
    found_it = False
    bioentity_id = bioentity_id.replace('"', "")
    for item in data:
        for association in item.get("assocs"):
            if association.get("subject").get("id") == bioentity_id:
                found_it = True
    assert found_it


@then(parsers.cfparse("the response should have {term:String} in the slim", extra_types=EXTRA_TYPES))
def term_in_slim(result, term):
    """
    Then the response should have {term} in the slim.

    :param result: The response object from the API call.
    :type result: TestResponse
    :param term: The expected slim term.
    :type term: str
    """
    data = result.json()
    found_it = False
    term = term.replace('"', "").strip()
    for item in data:
        for association in item.get("assocs"):
            if term in association.get("slim"):
                found_it = True
    assert found_it
