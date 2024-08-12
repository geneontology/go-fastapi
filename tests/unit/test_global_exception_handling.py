from fastapi.testclient import TestClient
from app.main import app

test_client = TestClient(app)


def test_value_error_handler():
    # Simulate an endpoint that raises a ValueError (e.g., by sending an invalid CURIE)
    response = test_client.get("/api/ontol/labeler?id=@base:invalid")

    # Verify that the global exception handler for ValueErrors, rewrites as an internal server error code.
    assert response.status_code == 400
    response = test_client.get(f"/api/gp/P05067/models")


def test_value_error_curie():
    response = test_client.get(f"/api/gp/P05067/models")
    assert response.status_code == 400
    assert response.json() == {"message": "Value error occurred: Invalid CURIE format"}


def test_ncbi_taxon_error_handling():
    response = test_client.get("/api/taxon/NCBITaxon%3A4896/models")
    assert response.status_code == 200
