from logging import raiseExceptions

from fastapi.testclient import TestClient

from app.exceptions.global_exceptions import DataNotFoundException
from app.main import app
import pytest

from app.middleware.logging_middleware import logger
from app.utils.golr_utils import is_valid_bioentity
from app.utils.ontology_utils import is_valid_goid

test_client = TestClient(app)


def test_value_error_handler():
    # Simulate an endpoint that raises a ValueError (e.g., by sending an invalid CURIE)
    response = test_client.get("/api/ontol/labeler?id=@base:invalid")

    # Verify that invalid IDs return 404 when not found
    assert response.status_code == 404
    response = test_client.get(f"/api/gp/P05067/models")
    assert response.status_code == 400

def test_value_error_curie():
    response = test_client.get(f"/api/gp/P05067/models")
    assert response.status_code == 400
    print(response.json())
    assert response.json() == {"detail": "Invalid CURIE format"}


def test_ncbi_taxon_success():
    response = test_client.get("/api/taxon/NCBITaxon%3A4896/models")
    assert response.status_code == 200


def test_ncbi_taxon_error_handling():
    response = test_client.get("/api/taxon/NCBITaxon%3AFAKE/models")
    assert response.status_code == 404


@pytest.mark.parametrize("endpoint", [
    "/api/bioentity/function/FAKE:12345",
    "/api/bioentity/function/FAKE:12345/taxons",
])
def test_get_bioentity_goid_not_found(endpoint):
    """
    Test that the DataNotFoundException is raised when the id does not exist.
    """
    # Perform the GET request
    response = test_client.get(endpoint)

    # Assert the status code is 400 (Invalid Request)
    assert response.status_code == 400, f"Endpoint {endpoint} failed with status code {response.status_code}"


@pytest.mark.parametrize("endpoint", [
    "/api/bioentity/FAKE:12345",
    "/api/bioentity/gene/FAKE:12345/function"
])
def test_get_bioentity_entity_id_not_found(endpoint):
    """
    Test that the DataNotFoundException is raised when the id does not exist.
    """
    # Perform the GET request
    response = test_client.get(endpoint)

    # Assert the status code is 404 (Not Found)
    assert response.status_code == 404, f"Endpoint {endpoint} failed with status code {response.status_code}"

@pytest.mark.parametrize("endpoint", [
    "/api/bioentity/function/FAKE:12345/genes",
])
def test_get_bioentity_genes_not_found(endpoint):
    """
    Test that the DataNotFoundException is raised when the id does not exist.
    """
    # Perform the GET request
    response = test_client.get(endpoint)

    # Assert the status code is 404 (Not Found)
    assert response.status_code == 400, f"Endpoint {endpoint} failed with status code {response.status_code}"


@pytest.mark.parametrize("goid,expected", [
    ("GO:0046330", True),  # Valid GO ID
    ("GO:zzzzz", False),  # Non-existent GO ID
    ("INVALID:12345", False),  # Invalid format
])
def test_is_valid_goid(goid, expected):
    """
    Test that the is_valid_goid function behaves as expected.
    """
    if expected:
        assert is_valid_goid(goid) == True
    else:
        try:
            result = is_valid_goid(goid)
            assert result == False
        except DataNotFoundException:
            assert not expected, f"GO ID {goid} raised DataNotFoundException as expected."
        except ValueError:
            assert not expected, f"GO ID {goid} raised ValueError as expected."


@pytest.mark.parametrize("entity_id,expected", [
    ("MGI:3588192", True),  # Valid ID
    ("ZFIN:ZDB-GENE-000403-1", True),  # Valid ID
    ("MGI:zzzzz", False),  # Invalid
    ("ZFIN:12345", False),  # Invalid
    ("HGNC:12345", False),  # Invalid
])
def test_is_valid_entity_id(entity_id, expected):
    """
    Test that the is_valid_goid function behaves as expected.
    """
    if expected:
        assert is_valid_bioentity(entity_id) == True
    else:
        try:
            result = is_valid_bioentity(entity_id)
            assert result == False
        except DataNotFoundException:
            logger.info("data not found exception")
            assert not expected, f"ID {entity_id} raised DataNotFoundException as expected."
        except ValueError:
            logger.info("value error")
            assert not expected, f"ID {entity_id} raised ValueError as expected."


@pytest.mark.parametrize(
    "goid,expected_status,expected_response",
    [
        ("GO:0008150", 200, {"key": "value"}),  # Example valid response
        ("INVALID:12345", 400, {"detail": "Invalid GO ID format"}),  # Invalid format
        ("GO:9999999", 404, {"detail": "Item with ID GO:9999999 not found"}),  # Non-existent GO ID
    ],
)
def test_get_annotations_by_goterm_id(goid, expected_status, expected_response):
    """
    Test the /api/bioentity/function/{id} endpoint.

    :param goid: The GO term ID to test.
    :param expected_status: Expected HTTP status code.
    :param expected_response: Expected JSON response.
    """
    # Perform the GET request
    response = test_client.get(
        f"/api/bioentity/function/{goid}"
    )

    # Assert the status code
    assert response.status_code == expected_status


def test_labeler_data_not_found_exception():
    """
    Test the labeler endpoint with "GO:0003677".

    :return: None
    """
    endpoint = "/api/ontol/labeler"
    data = {"id": "GO:zzzz"}
    response = test_client.get(endpoint, params=data)
    assert response.status_code == 404

ontology_endpoints = [f"/api/go/{id}/models",
                      ]


@pytest.mark.parametrize("endpoint", [
    "/api/go/FAKE:12345/models",
    "/api/go/FAKE:12345/hierarchy",
    "/api/go/FAKE:12345",
    "/api/association/between/FAKE:12345/FAKE:12345"
    # "/api/ontol/labeler",  # Uncomment if this endpoint should be included
])
def test_ontology_endpoints_not_found_error_handling(endpoint):
    """
    Test that the DataNotFoundException is raised when the id does not exist.
    """
    # Perform the GET request
    response = test_client.get(endpoint)

    # Assert the status code is 404 (Not Found)
    assert response.status_code == 400, f"Endpoint {endpoint} failed with status code {response.status_code}"


@pytest.mark.parametrize("endpoint", [
    "/api/go/GO:12345/models",
    "/api/go/GO:12345/hierarchy",
    "/api/go/GO:12345",
    "/api/association/between/GO:12345/GO:12345"
    # "/api/ontol/labeler",  # Uncomment if this endpoint should be included
])
def test_ontology_endpoints_not_found_error_handling(endpoint):
    """
    Test that the DataNotFoundException is raised when the id does not exist.
    """
    # Perform the GET request
    response = test_client.get(endpoint)

    # Assert the status code is 404 (Not Found)
    assert response.status_code == 404, f"Endpoint {endpoint} failed with status code {response.status_code}"