"""Tests for index-file loading and caching in app.utils.settings."""

import json

import pytest

from app.utils import settings
from app.utils.settings import (
    _load_index_file,
    clear_index_file_overrides,
    get_index_files,
    set_index_file_override,
)


@pytest.fixture(autouse=True)
def clean_index_state():
    """Start and end each test with no overrides and an empty cache."""
    clear_index_file_overrides()
    yield
    clear_index_file_overrides()


def test_cached_index_file_served_without_refetch():
    """A pre-seeded cache entry is returned as-is, without touching the configured URL."""
    sentinel = {"NCBITaxon:9606": ["model-1"]}
    settings.index_file_cache["gocam_taxon_index_file"] = sentinel
    # Served straight from the cache; the http(s) URL in config.yaml is never fetched.
    assert get_index_files("gocam_taxon_index_file") == sentinel
    # Identity is preserved across calls -> proves it is cached, not re-parsed each time.
    assert get_index_files("gocam_taxon_index_file") is sentinel


def test_clear_index_file_overrides_empties_cache():
    """clear_index_file_overrides() also drops cached content (test isolation / reload)."""
    settings.index_file_cache["gocam_taxon_index_file"] = {"x": []}
    clear_index_file_overrides()
    assert settings.index_file_cache == {}


def test_override_takes_precedence_over_cache(tmp_path):
    """A test override must win over any cached content and is itself never cached."""
    settings.index_file_cache["gocam_taxon_index_file"] = {"CACHED": ["should-not-win"]}
    override = tmp_path / "taxon.json"
    override.write_text(json.dumps({"NCBITaxon:7227": ["fly-model"]}))
    set_index_file_override("gocam_taxon_index_file", str(override))

    assert get_index_files("gocam_taxon_index_file") == {"NCBITaxon:7227": ["fly-model"]}
    # The override result is not written into the cache.
    assert settings.index_file_cache["gocam_taxon_index_file"] == {"CACHED": ["should-not-win"]}


def test_missing_key_raises_value_error():
    with pytest.raises(ValueError):
        get_index_files("gocam_definitely_not_a_real_index_file")


def test_local_file_loaded_once_then_cached(tmp_path):
    """A local-path index file is read once; later edits do not change the cached value."""
    f = tmp_path / "source.json"
    f.write_text(json.dumps({"PMID:1": ["m1"]}))
    config = {"gocam_source_index_file": {"url": str(f)}}

    first = _load_index_file("gocam_source_index_file", config)
    assert first == {"PMID:1": ["m1"]}

    # Mutating the file on disk must NOT be reflected -> confirms load-once caching.
    f.write_text(json.dumps({"PMID:1": ["m1"], "PMID:2": ["m2"]}))
    second = _load_index_file("gocam_source_index_file", config)
    assert second is first
    assert second == {"PMID:1": ["m1"]}
