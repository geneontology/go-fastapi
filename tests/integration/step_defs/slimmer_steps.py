from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then

from app.main import app

EXTRA_TYPES = {
    "String": str,
}


@scenario("../features/slimmer.feature", "slimmer routes work as expected")
def test_slim():
    # boilerplate
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
    test_client = TestClient(app)
    slimterms = slimterms.replace('"', "")
    slimterms_list = slimterms.split(",")
    data = {"subject": bioentity_id.replace('"', ""), "slim": slimterms_list}
    response = test_client.get("/api/bioentityset/slimmer/function", params=data)
    return response


# Then Steps


@then(parsers.parse('the response status code is "{code:d}"'))
def response_code(result, code):
    assert result.status_code == code


@then(
    parsers.cfparse(
        "the response should have an association with subject.label of {bioentity_label:String}",
        extra_types=EXTRA_TYPES,
    )
)
def subject_label(result, bioentity_label):
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
    data = result.json()
    found_it = False
    term = term.replace('"', "").strip()
    for item in data:
        for association in item.get("assocs"):
            if term in association.get("slim"):
                found_it = True
    assert found_it
