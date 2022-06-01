import logging

from ontobio.sparql.sparql_ontol_utils import SEPARATOR
from ontobio.ontol_factory import OntologyFactory
from ..settings import get_biolink_config

cfg = get_biolink_config()
omap = {}


def get_ontology(id):
    handle = id
    for c in cfg['ontologies']:
        if c['id'] == id:
            logging.info("getting handle for id: {} from cfg".format(id))
            handle = c['handle']

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
            "GO:0008289"
        ]
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
            "GO:0007610"
        ]
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
            "GO:0032991"
        ]
    }
]


def go_summary(goid):
    goid = correct_goid(goid)
    return """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
    PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>

    SELECT ?goid ?label ?definition ?comment ?creation_date		(GROUP_CONCAT(distinct ?synonym;separator='""" + SEPARATOR + """') as ?synonyms)
                                                                (GROUP_CONCAT(distinct ?relatedSynonym;separator='""" + SEPARATOR + """') as ?relatedSynonyms)
                                                                (GROUP_CONCAT(distinct ?alternativeId;separator='""" + SEPARATOR + """') as ?alternativeIds)
                                                                (GROUP_CONCAT(distinct ?xref;separator='""" + SEPARATOR + """') as ?xrefs)
                                                                (GROUP_CONCAT(distinct ?subset;separator='""" + SEPARATOR + """') as ?subsets)

    WHERE {
        BIND(<http://purl.obolibrary.org/obo/""" + goid + """> as ?goid) .
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


def correct_goid(goid):
    return goid.replace(":", "_")


def get_go_subsets(goid):
    goid = correct_goid(goid)
    return """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX obo: <http://www.geneontology.org/formats/oboInOwl#>

    SELECT ?label ?subset

    WHERE {
        BIND(<http://purl.obolibrary.org/obo/""" + goid + """> as ?goid) .
        optional { ?goid obo:inSubset ?subset .
                   ?subset rdfs:comment ?label } .
    }
    """