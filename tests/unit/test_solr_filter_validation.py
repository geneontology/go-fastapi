"""
Caller-supplied values before they reach a GOlr query.

Identifiers (evidence, taxon, id) land in a quoted fq phrase; free text
(autocomplete) lands in q. Hostile inputs are the scanner's own probes plus one planted example per
disallowed character, so each test exercises the character rather than
trusting a list to contain it.
"""

import time
from urllib.parse import quote, unquote_plus

import pytest
from fastapi.testclient import TestClient

from app.exceptions.global_exceptions import InvalidIdentifier
from app.main import app
from app.utils.golr_utils import (
    run_solr_on,
    solr_encode_query_value,
    solr_escape_query_syntax,
    solr_phrase_filter,
    solr_prefix_query,
    validate_solr_filter_values,
)
from app.utils.settings import ESOLR, ESOLRDoc

test_client = TestClient(app)

# --- identifiers ------------------------------------------------------------

# Values seen in production responses for the fields the filters address.
STORED_FIELD_VALUES = {
    "evidence_closure": ["ECO:0000314", "ECO:0000318", "ECO:0000501"],
    "taxon": ["NCBITaxon:9606", "NCBITaxon:7955", "NCBITaxon:10090"],
    "taxon_subset_closure": ["NCBITaxon:9606"],
}

# Document ids of the shapes the GO db-xref registry defines (go-site metadata/db-xrefs.yaml).
STORED_ID_SHAPES = [
    "GO:0008150",
    "GO_0008150",
    "ZFIN:ZDB-GENE-990415-44",
    "MGI:MGI:3588192",
    "UniProtKB:P08887-2",
    "UniProtKB:P08887-PRO_0000012345",
    "RNAcentral:URS00000B2A2E_9606",
    "RNAcentral:URS00000B2A2E/9606",
    "PomBase:SPAC1002.19",
    "dictyBase:DDB_G0267178",
    "TAIR:locus:2032970",
    "ComplexPortal:CPX-1234",
    "ZFIN:ZDB-PUB-060503-2",
]

# Well-formed but not stored anywhere: must still reach Solr and match nothing.
WELL_FORMED_UNKNOWN_VALUES = ["NONEXISTENT_CODE", "ECO:9999999", "base:invalid"]

# Probes the Red Agent used against production, verbatim.
FILTER_PROBES = [
    'NONEXISTENT_CODE" OR *:* OR "',
    'NONEXISTENT_CODE" OR evidence_type:"IDA',
    'NCBITaxon:9606" OR taxon:"NCBITaxon:10090',
]

# Probes against id lookups (fq=id:"…"), verbatim from the same scan, plus the
# GO-prefixed shape that passes the GO id prefix check.
ID_PROBES = [
    'GO:9999999" OR annotation_class:"GO:0008150',
    'GO:9999999" OR annotation_class_label:binding OR annotation_class:"GO:9999998',
    'GO:9999999" OR _val_:"sum(1,1)',
    'GO:0003677" OR annotation_class_label:"biological_process',
    'GO:NONEXISTENT" OR *:* OR "',
]

# One planted example per character outside the identifier grammar. Only the
# first group can end a quoted phrase; the second alters the raw query string;
# the rest are refused because no identifier contains them.
PHRASE_ENDING_CHARACTERS = ['"', "\\"]
QUERY_STRING_CHARACTERS = ["&", "#", "?", "%", "+", " "]
OTHER_DISALLOWED_CHARACTERS = ["(", ")", "*", "=", "{", "}", ",", "|", "\r", "\n", "\x00", "é"]
DISALLOWED_CHARACTERS = PHRASE_ENDING_CHARACTERS + QUERY_STRING_CHARACTERS + OTHER_DISALLOWED_CHARACTERS


@pytest.mark.parametrize("field, values", STORED_FIELD_VALUES.items())
def test_stored_field_values_pass_through_unchanged(field, values):
    """Validation must not alter what Solr is asked for."""
    assert validate_solr_filter_values(values, field) == values


@pytest.mark.parametrize("value", STORED_ID_SHAPES + WELL_FORMED_UNKNOWN_VALUES)
def test_identifier_shapes_pass(value):
    """Every registered id shape, and harmless unknown values, are accepted."""
    assert validate_solr_filter_values([value], "id") == [value]


def test_absent_filter_stays_absent():
    """None means no fq clause; it must survive as None for callers that pass it on."""
    assert validate_solr_filter_values(None, "taxon") is None
    assert solr_phrase_filter("evidence_closure", None) == ""


@pytest.mark.parametrize("value", FILTER_PROBES + ID_PROBES)
def test_scanner_probes_are_rejected(value):
    """Every probe that steered a query in production is refused before any query is built."""
    with pytest.raises(InvalidIdentifier) as excinfo:
        validate_solr_filter_values([value], "evidence")
    assert excinfo.value.status_code == 400


@pytest.mark.parametrize("char", DISALLOWED_CHARACTERS)
def test_each_disallowed_character_is_rejected(char):
    """Plant the character in an otherwise valid identifier; it must be refused."""
    with pytest.raises(InvalidIdentifier):
        validate_solr_filter_values(["ECO:0000314" + char + "x"], "evidence")


def test_empty_value_is_rejected():
    """An empty string is not an identifier."""
    with pytest.raises(InvalidIdentifier):
        validate_solr_filter_values([""], "evidence")


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
@pytest.mark.parametrize("value", FILTER_PROBES)
def test_filter_routes_refuse_probes_with_400(path, param, value):
    """Refusal happens before the GO id lookup, so this needs no network."""
    response = test_client.get(path, params={param: value})

    assert response.status_code == 400
    assert param in response.json()["detail"]


@pytest.mark.parametrize("value", ID_PROBES)
def test_id_lookup_refuses_probes_before_any_query(value):
    """run_solr_on validates before fetching, so no network and no retry delay."""
    started = time.monotonic()
    with pytest.raises(InvalidIdentifier):
        run_solr_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, value, "id")
    # The retry wrapper makes three attempts with two 2 s sleeps on anything whose
    # text contains "400"; validation must sit outside it.
    assert time.monotonic() - started < 1.0


@pytest.mark.parametrize(
    "path, params",
    [
        ("/api/ontology/term/{probe}", None),
        ("/api/ontology/term/{probe}/graph", None),
        ("/api/ontol/labeler", {"id": "{probe}"}),
        ("/api/bioentity/{probe}", None),
        ("/api/bioentity/gene/{probe}/function", None),
        ("/api/bioentity/function/{probe}", None),
        ("/api/bioentity/function/{probe}/genes", None),
        ("/api/bioentity/function/{probe}/taxons", None),
        ("/api/association/between/{probe}/GO:0016070", None),
        ("/api/taxon/{probe}/models", None),
        ("/api/gp/{probe}/models", None),
        ("/api/ontology/ribbon", {"subject": "{probe}"}),
    ],
)
@pytest.mark.parametrize("probe", ID_PROBES)
def test_id_routes_refuse_probes_with_400(path, params, probe):
    """Every route that puts a caller-supplied id into a quoted fq refuses a quoted breakout."""
    if params is not None:
        params = {k: v.format(probe=probe) for k, v in params.items()}
    response = test_client.get(path.format(probe=probe), params=params)

    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


# --- free text (autocomplete) -----------------------------------------------

# Real terms observed in the production access logs (see test_solr_encoding.py).
CURATOR_TERMS = [
    "KRAS", "Ppargc1a", "GO:0045087", "WB:WBGene00003622", "UniProtKB:P14713", "ceh-20",
    "asparagine--tRNA", "hydroxyacyl-CoA dehydratase", "cellular import/export",
    "mitochondrial biogenesis", "3-hydroxyacyl-CoA dehydrogenase (NAD+)", "protein+kinase", "shh",
]

# Probes the Red Agent used against the autocomplete route, verbatim.
AUTOCOMPLETE_PROBES = [
    "zzzznotexist12345 OR *:*",
    "*:*",
    "?",
    "zzzznotexist12345 OR ?",
    "bioentity_label_searchable:*",
    "DNA AND taxon:NCBITaxon\\:7955",
    "{!dismax qf=bioentity_name_searchable}test",
    "{!lucene df=bioentity_label}BRCA1",
    '{!edismax qf=bioentity_label_searchable uf=*}test _query_:"{!lucene}*:*"',
]


@pytest.mark.parametrize("term", CURATOR_TERMS)
def test_real_search_terms_are_not_escaped(term):
    """No real term carries query syntax, so none may change."""
    assert solr_escape_query_syntax(term) == term


@pytest.mark.parametrize("char", ["*", "?", "{", "}", "\\"])
def test_each_query_syntax_character_is_escaped(char):
    """Plant the character; it must come out backslash-escaped and nothing else may change."""
    assert solr_escape_query_syntax("shh" + char + "x") == "shh\\" + char + "x"


def test_trailing_backslash_cannot_escape_the_appended_wildcard():
    """A term ending in a backslash must not swallow the "*" the router appends."""
    assert (solr_escape_query_syntax("shh\\") + "*").endswith("\\\\*")


@pytest.mark.parametrize("probe", AUTOCOMPLETE_PROBES)
def test_probes_carry_no_unescaped_syntax_after_escaping(probe):
    """Every "*", "{" or "}" in a probe is preceded by a backslash once escaped."""
    escaped = solr_escape_query_syntax(probe)
    for index, char in enumerate(escaped):
        if char in "*?{}":
            assert escaped[index - 1] == "\\"


@pytest.mark.parametrize(
    "term, expected",
    [
        ("shh", "shh*"),
        ("protein+kinase", "protein+kinase*"),  # "+" decodes to a space downstream; verified live to match
        ("zzzz OR ", "zzzz%20OR*"),  # trailing space would leave "*" as its own clause
        ("zzzz+OR+", "zzzz+OR*"),  # trailing "+" is a trailing space once decoded
        ("shh\\", "shh%5C%5C*"),
    ],
)
def test_prefix_query_keeps_the_wildcard_attached(term, expected):
    """The router's "*" must always extend the caller's last token, never stand alone."""
    assert solr_prefix_query(term) == expected


@pytest.mark.parametrize("term", ["", "+", " ", "++ ", "\t"])
def test_prefix_query_refuses_terms_with_nothing_to_search(term):
    """Alone, these would leave q equal to "*"."""
    with pytest.raises(InvalidIdentifier):
        solr_prefix_query(term)


@pytest.mark.parametrize("term", ["+", " ", "++"])
def test_autocomplete_route_refuses_empty_terms_with_400(term):
    """No network: the refusal happens before the query is built."""
    response = test_client.get("/api/search/entity/autocomplete/" + quote(term, safe=""))

    assert response.status_code == 400


def test_escaping_then_encoding_round_trips():
    """The encoder must carry the escapes through unchanged."""
    escaped = solr_escape_query_syntax("zzz OR *:*")
    assert unquote_plus(solr_encode_query_value(escaped)) == escaped


@pytest.mark.integration
@pytest.mark.parametrize("probe", AUTOCOMPLETE_PROBES)
def test_live_autocomplete_probes_match_nothing(probe):
    """Against GOlr: each probe, which returned records in production, now matches no document."""
    response = test_client.get("/api/search/entity/autocomplete/" + quote(probe, safe=""), params={"rows": 3})

    assert response.status_code == 200
    assert response.json()["docs"] == []


@pytest.mark.integration
@pytest.mark.parametrize("term", ["shh", "WB:WBGene00003622", "KRAS", "actin"])
def test_live_autocomplete_real_terms_still_match(term):
    """Against GOlr: real terms keep returning documents."""
    response = test_client.get(f"/api/search/entity/autocomplete/{term}", params={"rows": 3})

    assert response.status_code == 200
    assert response.json()["docs"]


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
