# Test Fixtures

This directory contains test data files that are used by the unit tests to avoid dependencies on external services and file paths.

## Purpose

These fixture files allow tests to run in CI/CD environments where:
- External services (like Golr) may not be available or reliable
- File paths configured in `config.yaml` don't exist (e.g., `/tmp/test-output/`)
- We want fast, deterministic tests that don't depend on network conditions

## How It Works

The `tests/conftest.py` file automatically sets up overrides for all index files during test execution using pytest hooks:
- `pytest_configure`: Runs once at test session start, sets up file path overrides
- `pytest_unconfigure`: Runs once at test session end, clears overrides

The `app/utils/settings.py` module supports index file overrides via:
- `set_index_file_override(file_key, file_path)`: Set a custom path for an index file
- `clear_index_file_overrides()`: Clear all overrides
- `get_index_files(file_key)`: Checks overrides first, then falls back to config.yaml

## Fixture Files

### taxon_index.json
Maps NCBI Taxon IDs to GO-CAM model IDs.

**Usage**: Tests for `/api/taxon/{taxon}/models` endpoint
**Format**:
```json
{
  "NCBITaxon:9606": ["model_id_1", "model_id_2", ...],
  "NCBITaxon:4896": ["model_id_1", ...]
}
```

### entity_index.json
Maps gene/protein identifiers to GO-CAM model IDs. Includes both CURIE and IRI forms.

**Usage**: Tests for `/api/gp/{id}/models` and ontology endpoints
**Format**:
```json
{
  "WB:WBGene00002147": ["59a6110e00000067"],
  "http://identifiers.org/wormbase/WBGene00002147": ["59a6110e00000067"]
}
```

### contributor_index.json
Maps ORCID IDs to GO-CAM model IDs.

**Usage**: Contributor-related endpoints (if any)
**Format**:
```json
{
  "http://orcid.org/0000-0001-XXXX-XXXX": ["model_id_1", ...]
}
```

### source_index.json
Maps publication identifiers (PMIDs) to GO-CAM model IDs.

**Usage**: Tests for `/api/pmid/{id}/models` endpoint
**Format**:
```json
{
  "PMID:15314168": ["59a6110e00000067"]
}
```

### evidence_index.json
Maps Evidence Ontology (ECO) codes to GO-CAM model IDs.

**Usage**: Evidence-related endpoint tests
**Format**:
```json
{
  "ECO:0000314": ["model_id_1", "model_id_2"]
}
```

## Adding New Test Data

When adding new tests that require index files:

1. **Use real GO-CAM model IDs** that exist in the S3 bucket (e.g., `59a6110e00000067`, `66187e4700001573`, `581e072c00000820`)
2. **Add both CURIE and IRI forms** for entity_index.json (tests use both formats)
3. **Keep test data minimal** - only include data needed for tests to pass
4. **Update this README** if you add new fixture files

## Verifying Real Model IDs

To check if a GO-CAM model ID is valid:
```bash
curl -I "https://go-public.s3.amazonaws.com/files/go-cam/{model_id}.json"
```

If you get HTTP 200, the model exists. If you get 403/404, choose a different ID.

## Local vs CI Behavior

- **Local development**: Uses real paths from `config.yaml` by default, unless running tests
- **Test execution**: Automatically uses fixture files via conftest.py
- **CI/CD**: Uses fixture files, avoiding file not found errors