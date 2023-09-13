"""ontology utility functions."""
import logging

from linkml_runtime.utils.namespaces import Namespaces
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.implementations.sparql.sparql_query import SparqlQuery
from oaklib.resource import OntologyResource
from ontobio.golr.golr_query import ESOLR, ESOLRDoc
from ontobio.ontol_factory import OntologyFactory
from ontobio.sparql.sparql_ontol_utils import SEPARATOR

from app.utils.golr_utils import gu_run_solr_text_on
from app.utils.settings import get_golr_config, get_sparql_endpoint

cfg = get_golr_config()
omap = {}

aspect_map = {"P": "GO:0008150", "F": "GO:0003674", "C": "GO:0005575"}
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


def batch_fetch_labels(ids):
    """
    Fetch all rdfs:label assertions for a set of CURIEs.

    :param ids: List of CURIEs for which labels are to be fetched.
    :type ids: list
    :return: Dictionary containing the CURIEs as keys and their corresponding labels as values.
    :rtype: dict
    """
    m = {}
    for id in ids:
        if id.startswith("MGI:"):
            id = "MGI:" + id
        label = goont_fetch_label(id)
        if label is not None:
            m[id] = label
    return m


def goont_fetch_label(id):
    """
    Fetch all rdfs:label assertions for a URI.

    :param id: The URI for which the label is to be fetched.
    :type id: str
    :return: List of labels for the given URI.
    :rtype: list
    """
    ns = Namespaces()
    ns.add_prefixmap("go")
    iri = ns.uri_for(id)
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = SparqlQuery(select=["?label"], where=["<" + iri + "> rdfs:label ?label"])
    bindings = si._sparql_query(query.query_str())
    rows = [r["label"]["value"] for r in bindings]
    return rows[0]


def get_ontology_subsets_by_id(id: str):
    """
    Get ontology subsets based on the provided identifier.

    :param id: The identifier for the ontology subset.
    :type id: str
    :return: List of ontology subsets.
    :rtype: list
    """
    q = "*:*"
    qf = ""
    fq = "&fq=subset:" + id
    fields = "annotation_class,annotation_class_label,description,source"

    # This is a temporary fix while waiting for the PR of the AGR slim on go-ontology
    if id == "goslim_agr":
        terms_list = set()
        for section in agr_slim_order:
            terms_list.add(section["category"])
            for term in section["terms"]:
                terms_list.add(term)

        goslim_agr_ids = '" "'.join(terms_list)
        fq = '&fq=annotation_class:("' + goslim_agr_ids + '")'

    fq = fq + "&rows=1000"
    data = gu_run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq, False)

    tr = {}
    for term in data:
        source = term["source"]
        if source not in tr:
            tr[source] = {"annotation_class_label": source, "terms": []}
        ready_term = term.copy()
        del ready_term["source"]
        tr[source]["terms"].append(ready_term)

    cats = []
    for category in tr:
        cats.append(category)

    fq = "&fq=annotation_class_label:(" + " or ".join(cats) + ")&rows=1000"
    data = gu_run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq, False)

    for category in tr:
        for temp in data:
            if temp["annotation_class_label"] == category:
                tr[category]["annotation_class"] = temp["annotation_class"]
                tr[category]["description"] = temp["description"]
                break

    result = []
    for category in tr:
        cat = tr[category]
        result.append(cat)

        # if goslim_agr, reorder the list based on the temporary json object below
    if id == "goslim_agr":
        temp = []
        for agr_category in agr_slim_order:
            cat = agr_category["category"]
            for category in result:
                if category["annotation_class"] == cat:
                    ordered_terms = []
                    for ordered_term in agr_category["terms"]:
                        for unordered_term in category["terms"]:
                            if unordered_term["annotation_class"] == ordered_term:
                                ordered_terms.append(unordered_term)
                                break
                    category["terms"] = ordered_terms
                    temp.append(category)
        result = temp

    return result


def get_category_terms(category):
    """
    Get category terms based on the provided category.

    :param category: The category for which terms are to be fetched.
    :type category: dict
    :return: List of terms for the given category.
    :rtype: list
    """
    terms = []
    for group in category["groups"]:
        if group["type"] == "Term":
            terms.append(group)
    return terms


def get_ontology(id):
    """
    Get ontology based on the provided identifier.

    :param id: The identifier for the ontology.
    :type id: str
    :return: Ontology object.
    :rtype: Ontology
    """
    handle = id
    for c in cfg["ontologies"]:
        if c["id"] == id:
            print("getting handle for id: {} from cfg".format(id))
            handle = c["handle"]

    if handle not in omap:
        logging.info("Creating a new ontology object for {}".format(handle))
        ofa = OntologyFactory()
        omap[handle] = ofa.create(handle)
    else:
        logging.info("Using cached for {}".format(handle))

    print("handle: " + handle)
    return omap[handle]


# this is a temporary json object, while waiting the
# ontology gets an annotation field to specify the order of a term in a slim
agr_slim_order = [
    {
        "category": "GO:0003674",
        "terms": [
            "GO:0003824",
            "GO:0030234",
            "GO:0038023",
            "GO:0005102",
            "GO:0005215",
            "GO:0005198",
            "GO:0008092",
            "GO:0003677",
            "GO:0003723",
            "GO:0003700",
            "GO:0008134",
            "GO:0036094",
            "GO:0046872",
            "GO:0030246",
            "GO:0097367",
            "GO:0008289",
        ],
    },
    {
        "category": "GO:0008150",
        "terms": [
            "GO:0007049",
            "GO:0016043",
            "GO:0051234",
            "GO:0008283",
            "GO:0030154",
            "GO:0008219",
            "GO:0032502",
            "GO:0000003",
            "GO:0002376",
            "GO:0050877",
            "GO:0050896",
            "GO:0023052",
            "GO:0006259",
            "GO:0016070",
            "GO:0019538",
            "GO:0005975",
            "GO:1901135",
            "GO:0006629",
            "GO:0042592",
            "GO:0009056",
            "GO:0007610",
        ],
    },
    {
        "category": "GO:0005575",
        "terms": [
            "GO:0005576",
            "GO:0005886",
            "GO:0045202",
            "GO:0030054",
            "GO:0042995",
            "GO:0031410",
            "GO:0005768",
            "GO:0005773",
            "GO:0005794",
            "GO:0005783",
            "GO:0005829",
            "GO:0005739",
            "GO:0005634",
            "GO:0005694",
            "GO:0005856",
            "GO:0032991",
        ],
    },
]


def create_go_summary_sparql(goid):
    """
    Create SPARQL query for fetching GO summary.

    :param goid: The GO identifier for which the summary is to be fetched.
    :type goid: str
    :return: SPARQL query string.
    :rtype: str
    """
    goid = correct_goid(goid)
    return (
        """
    PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
    PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>

    SELECT ?goid ?label ?definition ?comment ?creation_date		(GROUP_CONCAT(distinct ?synonym;separator='"""
        + SEPARATOR
        + """') as ?synonyms)
                                                                (GROUP_CONCAT(distinct ?relatedSynonym;separator='"""
        + SEPARATOR
        + """') as ?relatedSynonyms)
                                                                (GROUP_CONCAT(distinct ?alternativeId;separator='"""
        + SEPARATOR
        + """') as ?alternativeIds)
                                                                (GROUP_CONCAT(distinct ?xref;separator='"""
        + SEPARATOR
        + """') as ?xrefs)
                                                                (GROUP_CONCAT(distinct ?subset;separator='"""
        + SEPARATOR
        + """') as ?subsets)

    WHERE {
        BIND(<http://purl.obolibrary.org/obo/"""
        + goid
        + """> as ?goid) .
        optional { ?goid rdfs:label ?label } .
        optional { ?goid definition: ?definition } .
        optional { ?goid rdfs:comment ?comment } .
        optional { ?goid obo:creation_date ?creation_date } .
        optional { ?goid obo:hasAlternativeId ?alternativeId } .
        optional { ?goid obo:hasRelatedSynonym ?relatedSynonym } .
        optional { ?goid obo:hasExactSynonym ?synonym } .
        optional { ?goid obo:hasDbXref ?xref } .
        optional { ?goid obo:inSubset ?subset } .
    }
    GROUP BY ?goid ?label ?definition ?comment ?creation_date
    """
    )


def correct_goid(goid):
    """
    Correct the format of the GO identifier.

    :param goid: The GO identifier to be corrected.
    :type goid: str
    :return: Corrected GO identifier.
    :rtype: str
    """
    return goid.replace(":", "_")


def get_purl(goid):
    """
    Retrieve the PURL for the GO identifier.

    :param goid: The GO identifier to be corrected.
    :type goid: str
    :return: URI for goid.
    :rtype: str
    """
    goid = correct_goid(goid)
    return "http://purl.obolibrary.org/obo/" + goid


def get_go_subsets_sparql_query(goid):
    """
    Create SPARQL query for fetching GO subsets.

    :param goid: The GO identifier for which the subsets are to be fetched.
    :type goid: str
    :return: SPARQL query string.
    :rtype: str
    """
    goid = correct_goid(goid)
    return (
        """
    PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>

    SELECT ?label ?subset

    WHERE {
        BIND(<http://purl.obolibrary.org/obo/"""
        + goid
        + """> as ?goid) .
        optional { ?goid obo:inSubset ?subset .
                   ?subset rdfs:comment ?label } .
    }
    """
    )
