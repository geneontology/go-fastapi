"""Pytest configuration and fixtures for tests."""

import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """
    Pytest hook that runs once at the start of the test session.

    This sets up test index file overrides so tests use fixture data
    instead of the paths configured in config.yaml.
    """
    from app.utils.settings import set_index_file_override
    from app.utils.rate_limiter import get_rate_limiter
    
    # Set up slower rate limiting for tests to avoid hitting GOLr API limits
    # This will ensure at least 3 seconds between each GOLr API call
    golr_limiter = get_rate_limiter("golr", calls_per_second=0.33)

    # Get the path to the fixtures directory
    fixtures_dir = Path(__file__).parent / "fixtures"

    # Set up overrides for all index files
    index_files = {
        "gocam_taxon_index_file": "taxon_index.json",
        "gocam_entity_index_file": "entity_index.json",
        "gocam_contributor_index_file": "contributor_index.json",
        "gocam_source_index_file": "source_index.json",
        "gocam_evidence_index_file": "evidence_index.json",
    }

    for key, filename in index_files.items():
        file_path = fixtures_dir / filename
        if file_path.exists():
            set_index_file_override(key, str(file_path))


def pytest_unconfigure(config):
    """
    Pytest hook that runs once at the end of the test session.

    Clears the index file overrides.
    """
    from app.utils.settings import clear_index_file_overrides
    clear_index_file_overrides()