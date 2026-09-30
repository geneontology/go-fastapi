"""
Caller-supplied filter values (evidence, taxon) before they reach a GOlr fq clause.

Legitimate values are identifiers seen in production responses and documentation.
Hostile values are the scanner's own probes plus one planted example per character
that can close a quoted phrase or start another query-string parameter; each test
plants the character rather than trusting a list to contain it.
"""

import pytest
from fastapi.testclient import TestClient

from app.exceptions.global_exceptions import InvalidIdentifier
from app.main import app
from app.utils.golr_utils import solr_phrase_filter, validate_solr_filter_values

test_client = TestClient(app)

# Values GOlr actually stores in evidence_closure / taxon / taxon_subset_closure,
# plus the publication form the /taxons docstring advertises.
LEGITIMATE_VALUES = [
    "ECO:0000314",
    "ECO:0000501",
    "NCBITaxon:9606",
    "NCBITaxon:7955",
    "ZFIN:ZDB-PUB-060503-2",
    "GO:0044598",
    "goslim_generic",
    "NONEXISTENT_CODE",  # harmless and wrong: must still reach Solr and match nothing
]

# Probes the Red Agent used against production, verbatim.
SCANNER_PROBES = [
    'NONEXISTENT_CODE" OR *:* OR "',
    'NONEXISTENT_CODE" OR evidence_type:"IDA',
    'NCBITaxon:9606" OR taxon:"NCBITaxon:10090',
]

# One character each that has meaning inside a quoted Solr phrase or a URL query string.
PHRASE_BREAKING_CHARACTERS = [
    '"', "\\", " ", "(", ")", "*", "&", "=", "?", "#", "{", "}", "+", "%", "/", "\r", "\n", "\x00",
]


@pytest.mark.parametrize("value", LEGITIMATE_VALUES)
def test_legitimate_values_pass_through_unchanged(value):
    """Validation must not alter what Solr is asked for."""
    assert validate_solr_filter_values([value], "evidence") == [value]


def test_absent_filter_stays_absent():
    """None means no fq clause; it must survive as None for callers that pass it on."""
    assert validate_solr_filter_values(None, "taxon") is None
    assert solr_phrase_filter("evidence_closure", None) == ""


@pytest.mark.parametrize("value", SCANNER_PROBES)
def test_scanner_probes_are_rejected(value):
    """Every probe that steered the query in production is refused before any query is built."""
    with pytest.raises(InvalidIdentifier) as excinfo:
        validate_solr_filter_values([value], "evidence")
    assert excinfo.value.status_code == 400


@pytest.mark.parametrize("char", PHRASE_BREAKING_CHARACTERS)
def test_each_phrase_breaking_character_is_rejected(char):
    """Plant the character in an otherwise valid identifier; it must be refused."""
    with pytest.raises(InvalidIdentifier):
        validate_solr_filter_values(["ECO:0000314" + char + "x"], "evidence")


@pytest.mark.parametrize("value", ["", "ECO:0000314,ECO:0000501"])
def test_empty_and_comma_joined_values_are_rejected(value):
    """An empty value is not an identifier; a comma would join two phrases inside one."""
    with pytest.raises(InvalidIdentifier):
        validate_solr_filter_values([value], "evidence")


def test_one_bad_value_in_a_list_rejects_the_request():
    """Validation is per value, not per list."""
    with pytest.raises(InvalidIdentifier):
        validate_solr_filter_values(["ECO:0000314", 'x" OR *:* OR "'], "evidence")


def test_error_names_the_parameter():
    """The 400 has to tell the caller which parameter was refused."""
    with pytest.raises(InvalidIdentifier) as excinfo:
        validate_solr_filter_values(["a b"], "taxon")
    assert "taxon" in excinfo.value.detail


@pytest.mark.parametrize(
    "field, values, expected",
    [
        ("evidence_closure", ["ECO:0000314"], '&fq=evidence_closure:("ECO:0000314")'),
        ("evidence_closure", ["ECO:0000314", "ECO:0000501"], '&fq=evidence_closure:("ECO:0000314","ECO:0000501")'),
        ("taxon_subset_closure", ["NCBITaxon:9606"], '&fq=taxon_subset_closure:("NCBITaxon:9606")'),
        ("evidence_closure", [], ""),
    ],
)
def test_phrase_filter_keeps_the_historical_clause_shape(field, values, expected):
    """The clause must be byte-identical to what the routers built by hand before."""
    assert solr_phrase_filter(field, values) == expected


@pytest.mark.parametrize(
    "path, param",
    [
        ("/api/bioentity/function/GO:0044598", "evidence"),
        ("/api/bioentity/function/GO:0044598/taxons", "evidence"),
        ("/api/bioentity/function/GO:0044598/genes", "taxon"),
    ],
)
@pytest.mark.parametrize("value", SCANNER_PROBES)
def test_routes_refuse_probes_with_400(path, param, value):
    """Refusal happens before the GO id lookup, so this needs no network."""
    response = test_client.get(path, params={param: value})

    assert response.status_code == 400
    assert param in response.json()["detail"]


@pytest.mark.integration
def test_live_evidence_filter_still_constrains_results():
    """Against GOlr: a real code narrows the set, an unknown code empties it (the scanner's baseline)."""
    matched = test_client.get("/api/bioentity/function/GO:0044598", params={"rows": 5, "evidence": "ECO:0000501"})
    unmatched = test_client.get("/api/bioentity/function/GO:0044598", params={"rows": 5, "evidence": "ECO:9999999"})

    assert matched.status_code == 200
    assert {doc["evidence"] for doc in matched.json()} == {"ECO:0000501"}
    assert unmatched.status_code == 404


@pytest.mark.integration
def test_live_taxon_filter_still_constrains_results():
    """Against GOlr: every association comes back in the requested species."""
    response = test_client.get(
        "/api/bioentity/function/GO:0044598/genes", params={"rows": 5, "taxon": "NCBITaxon:9606"}
    )

    assert response.status_code == 200
    assert {assoc["subject"]["taxon"]["id"] for assoc in response.json()["associations"]} == {"NCBITaxon:9606"}
