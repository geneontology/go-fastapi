import pytest
from pytest_bdd import scenario, given, when, then, scenarios
from app.main import app
from fastapi.testclient import TestClient


@scenario('../features/bioentityfunction.feature',
          'User fetches all GO functional annotations for a zebrafish gene')
def test_add():
    # tests will be executed by the bioentity_function.feature steps
    pass


@given("the go-fastapi test-client is queried with a value")
def api_result():
    test_client = TestClient(app)
    response = test_client.get(f"/api/bioentity/gene/ZFIN%3AZDB-GENE-050417-357/function")
    return response.json()


@then("the endpoint should return successfully")
def endpoint_retuns():
    test_client = TestClient(app)
    response = test_client.get(f"/api/bioentity/gene/ZFIN%3AZDB-GENE-050417-357/function")
    assert response.status_code == 200

