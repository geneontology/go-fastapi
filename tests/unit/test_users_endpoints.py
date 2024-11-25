"""Unit tests for the users endpoints."""
import logging
from fastapi.testclient import TestClient
from app.main import app


logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

test_client = TestClient(app)
gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8", "MGI:3588192"]
go_cam_ids = ["gomodel:66187e4700001573", "66187e4700001573", "59a6110e00000067", "SYNGO_369",
              "581e072c00000820", "gomodel:59a6110e00000067", "gomodel:SYNGO_369"]
go_cam_not_found_ids = ["NGO_369", "581e072c000008", "gomodel:59a6110e000000",]
valid_orcids = ["0000-0003-1813-6857"]
invalid_orcids = ["FAKE_ORCID"]


def test_get_models_by_orcid():
    for orcid in valid_orcids:
        print(orcid)
        response = test_client.get(f"/api/users/{orcid}/models")
        assert response.status_code == 200  # Verify the status code
        data = response.json()
        assert len(data) >= 10  # Verify the length of the response, should be 11 for Pascale


def test_invalid_models_by_orcid():
    for orcid in invalid_orcids:
        response = test_client.get(f"/api/users/{orcid}/models")
        assert response.status_code == 404


