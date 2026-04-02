"""Unit and integration tests for golr_utils functions."""

import pytest

from app.utils.golr_utils import get_bioentity_isoforms


class TestFacetListParsing:
    """Tests for the facet list parsing logic in get_bioentity_isoforms."""

    @pytest.mark.parametrize(
        "facet_response, expected",
        [
            # Standard case: alternating [value, count, value, count, ...]
            (
                ["UniProtKB:P08887", 88, "UniProtKB:P08887-1", 15, "UniProtKB:P08887-2", 12],
                ["UniProtKB:P08887", "UniProtKB:P08887-1", "UniProtKB:P08887-2"],
            ),
            # Empty facet list
            ([], []),
            # Single isoform
            (["UniProtKB:P12345", 5], ["UniProtKB:P12345"]),
            # Facet list with empty string value (should be filtered out)
            (["UniProtKB:P08887", 88, "", 7, "UniProtKB:P08887-2", 12], ["UniProtKB:P08887", "UniProtKB:P08887-2"]),
        ],
        ids=["multiple_isoforms", "empty", "single", "filters_empty_strings"],
    )
    def test_parse_facet_list(self, facet_response, expected):
        """
        Test that the facet list parsing extracts values correctly from alternating [value, count, ...] format.

        This tests the parsing logic in isolation by verifying the list comprehension
        that extracts every other element (the values) from the Solr facet field response.
        """
        # This is the exact parsing logic from get_bioentity_isoforms
        result = [facet_response[i] for i in range(0, len(facet_response), 2) if facet_response[i]]
        assert result == expected


@pytest.mark.integration
def test_get_bioentity_isoforms_from_golr():
    """
    Test that get_bioentity_isoforms returns known isoforms for UniProtKB:P08887 from live GOlr.

    UniProtKB:P08887 (IL6R) is known to have isoform annotations including
    UniProtKB:P08887-2, which is the isoform referenced in GO-CAM models
    per https://github.com/geneontology/go-fastapi/issues/135.
    """
    isoforms = get_bioentity_isoforms("UniProtKB:P08887")
    assert isinstance(isoforms, list)
    assert len(isoforms) > 0
    # The canonical ID itself should appear in the facet results
    assert "UniProtKB:P08887" in isoforms
    # The isoform from issue #135 must be present
    assert "UniProtKB:P08887-2" in isoforms


@pytest.mark.integration
def test_gp_models_endpoint_returns_isoform_models():
    """
    Test that /api/gp/UniProtKB:P08887/models returns GO-CAM models for isoforms.

    This hits live Blazegraph and GOlr. The canonical ID UniProtKB:P08887 has no
    direct GO-CAM annotations, but its isoforms (e.g. UniProtKB:P08887-2) do.
    The endpoint should return models for all isoforms.
    See: https://github.com/geneontology/go-fastapi/issues/135
    """
    from fastapi.testclient import TestClient

    from app.main import app

    test_client = TestClient(app)
    response = test_client.get("/api/gp/UniProtKB:P08887/models")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    gocam_uris = {r["gocam"] for r in results}
    # These two models are specifically mentioned in issue #135
    assert "http://model.geneontology.org/5f46c3b700002685" in gocam_uris
    assert "http://model.geneontology.org/653b0ce600000016" in gocam_uris
