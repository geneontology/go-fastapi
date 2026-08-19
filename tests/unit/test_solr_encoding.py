"""Encoding of caller-supplied text before it reaches a GOlr query.

Legitimate terms are real ones from the production access logs, chosen to sit
far apart lexically. Two modelling details matter: decode with unquote_plus,
because the backend parses a query string and turns "+" into a space; and
plant each hostile character in an input rather than looking for it in the
term lists, which do not contain "?" or "#" or a quote.
"""

from urllib.parse import parse_qsl, unquote_plus

import pytest

from app.utils.golr_utils import solr_encode_query_value

# Real terms observed in the production access logs.
CURATOR_TERMS = [
    "KRAS",                        # uppercase human gene symbol
    "SYNGAP1",                     # symbol with a trailing digit
    "Ppargc1a",                    # mixed-case mouse symbol
    "Tfb2m",                       # short mixed-case with digit
    "GO:0045087",                  # GO CURIE
    "WB:WBGene00003622",           # WormBase CURIE
    "UniProtKB:P14713",            # UniProt CURIE
    "ceh-20",                      # hyphenated C. elegans gene name
    "unc-22",
    "dhr-96",
    "aspartyl-tRNA",               # hyphenated biochemical name
    "asparagine--tRNA",            # double hyphen
    "hydroxyacyl-CoA dehydratase",  # hyphen plus space
    "cellular import/export",      # slash
    "mitochondrial biogenesis",    # multi-word
    "MYNLSILETQKAIKFIKDLF",        # peptide sequence
    "phosphohistidine",            # plain lowercase word
    "shh",                         # short lowercase symbol
]

# Real injection attempts observed in the same logs.
INJECTION_TERMS = [
    "shh&rows=1",                  # the surface this change closes
    "*:*",
    "taxon_label:Homo",
    "zzzznotfound OR bioentity_name_searchable:kinase",
    "{!dismax qf=bioentity_label_searchable}actin",
]

# Characters that could start or steer another query-string parameter.
QUERY_STRING_METACHARACTERS = ["&", "=", "?", "#", ";", " ", '"', "{", "}", "\r", "\n", "\x00"]


def solr_sees(encoded_term: str) -> str:
    """Decode as the backend's query-string parser does, including "+" as space."""
    return unquote_plus(encoded_term)


@pytest.mark.parametrize("term", CURATOR_TERMS + INJECTION_TERMS)
def test_solr_still_sees_the_original_text(term):
    """Whatever Solr did with a term before, it does after."""
    assert solr_sees(solr_encode_query_value(term)) == term


@pytest.mark.parametrize("char", QUERY_STRING_METACHARACTERS)
def test_no_metacharacter_survives_encoding(char):
    """Plant each character in the input; none may come back out raw."""
    encoded = solr_encode_query_value("shh" + char + "rows=1")
    assert char not in encoded


@pytest.mark.parametrize("char", QUERY_STRING_METACHARACTERS)
def test_metacharacters_survive_as_data(char):
    """Encoding them must not lose them -- they are searched for, not dropped."""
    term = "shh" + char + "rows=1"
    assert solr_sees(solr_encode_query_value(term)) == term


@pytest.mark.parametrize(
    "term",
    ["shh&rows=1", "shh&hl.simple.pre=<img src=x>", "shh&fl=*", "shh&qt=/update"],
)
def test_no_second_parameter_can_be_created(term):
    """A term must stay one value of q, never become a parameter of its own."""
    query_string = "q=" + solr_encode_query_value(term) + "*" + "&qf=bioentity&rows=100"

    parsed = parse_qsl(query_string, keep_blank_values=True)

    assert [name for name, _ in parsed] == ["q", "qf", "rows"]
    assert dict(parsed)["q"] == term + "*"
    assert dict(parsed)["rows"] == "100"


@pytest.mark.parametrize(
    "term",
    ["GO:0045087", "WB:WBGene00003622", "ceh-20", "asparagine--tRNA", "cellular import/export"],
)
def test_query_syntax_is_preserved_not_neutralized(term):
    """Constraining Solr syntax is a separate change; this one must not do it by accident.

    WB:WBGene00003622 resolves today, and escaping its colon would stop it.
    """
    assert solr_sees(solr_encode_query_value(term)) == term


@pytest.mark.parametrize("term", ["protein+kinase", "sportusal+et+heparine", "a+b"])
def test_plus_still_reaches_solr_as_a_space(term):
    """Verified live: protein+kinase matches today and returns none if encoded."""
    assert solr_encode_query_value(term) == term
    assert solr_sees(solr_encode_query_value(term)) == term.replace("+", " ")


def test_percent_in_input_is_not_double_decoded():
    """A literal percent must survive as a percent, not become an escape."""
    assert solr_sees(solr_encode_query_value("100%")) == "100%"
    assert solr_sees(solr_encode_query_value("%26rows=1")) == "%26rows=1"


def test_encoding_is_not_idempotent_and_must_be_applied_once():
    """Encoding an encoded value escapes its percents again, changing what is searched."""
    once = solr_encode_query_value("GO:0045087")
    twice = solr_encode_query_value(once)

    assert solr_sees(once) == "GO:0045087"
    assert solr_sees(twice) == once != "GO:0045087"
