import logging

from linkml_runtime.utils.namespaces import Namespaces
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.implementations.sparql.sparql_query import SparqlQuery
from oaklib.resource import OntologyResource
from ontobio.golr.golr_query import ESOLR, ESOLRDoc, run_solr_text_on
from ontobio.ontol_factory import OntologyFactory
from ontobio.sparql.sparql_ontol_utils import SEPARATOR

from app.utils.settings import get_golr_config

cfg = get_golr_config()
omap = {}

aspect_map = {"P": "GO:0008150", "F": "GO:0003674", "C": "GO:0005575"}
logger = logging.getLogger(__name__)


def batch_fetch_labels(ids):
    """
    fetch all rdfs:label assertions for a set of CURIEs
    """
    m = {}
    for id in ids:
        label = goont_fetch_label(id)
        if label is not None:
            m[id] = label
    return m


def goont_fetch_label(id):
    """
    fetch all rdfs:label assertions for a URI
    """
    ns = Namespaces()
    ns.add_prefixmap("go")
    iri = ns.uri_for(id)
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
    si = SparqlImplementation(ont_r)
    query = SparqlQuery(select=["?label"], where=["<" + iri + "> rdfs:label ?label"])
    logger.info(query.query_str())
    bindings = si._sparql_query(query.query_str())
    print(bindings)
    rows = [r["label"]["value"] for r in bindings]
    return rows[0]


def get_ontology_subsets_by_id(id: str):
    q = "*:*"
    qf = ""
    fq = "&fq=subset:" + id + "&rows=1000"
    fields = "annotation_class,annotation_class_label,description,source"

    # This is a temporary fix while waiting for the PR of the AGR slim on go-ontology
    if id == "goslim_agr":
        terms_list = set()
        for section in agr_slim_order:
            terms_list.add(section["category"])
            for term in section["terms"]:
                terms_list.add(term)

        goslim_agr_ids = '" "'.join(terms_list)
        fq = '&fq=annotation_class:("' + goslim_agr_ids + '")&rows=1000'

    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq)

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
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ONTOLOGY, q, qf, fields, fq)

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
                    for ot in agr_category["terms"]:
                        for uot in category["terms"]:
                            if uot["annotation_class"] == ot:
                                ordered_terms.append(uot)
                                break
                    category["terms"] = ordered_terms
                    temp.append(category)
        result = temp

    return result


def get_category_terms(category):
    terms = []
    for group in category["groups"]:
        if group["type"] == "Term":
            terms.append(group)
    return terms


def get_ontology(id):
    handle = id
    for c in cfg["ontologies"]:
        if c["id"] == id:
            logging.info("getting handle for id: {} from cfg".format(id))
            handle = c["handle"]

    if handle not in omap:
        logging.info("Creating a new ontology object for {}".format(handle))
        ofa = OntologyFactory()
        omap[handle] = ofa.create(handle)
    else:
        logging.info("Using cached for {}".format(handle))

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
    return goid.replace(":", "_")


def get_go_subsets_sparql_query(goid):
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
