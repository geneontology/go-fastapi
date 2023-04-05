import logging
from enum import Enum
from pprint import pprint
from typing import List

from fastapi import APIRouter, Query
from linkml_runtime.utils.namespaces import Namespaces
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from ontobio.config import get_config
from ontobio.golr.golr_associations import search_associations
from ontobio.util.user_agent import get_user_agent

from app.utils.golr.golr_utls import run_solr_text_on
from app.utils.settings import ESOLR, ESOLRDoc

from .slimmer import gene_to_uniprot_from_mygene

log = logging.getLogger(__name__)

INVOLVED_IN = "involved_in"
ACTS_UPSTREAM_OF_OR_WITHIN = "acts_upstream_of_or_within"
FUNCTION_CATEGORY = "function"
ANATOMY_CATEGORY = "anatomy"
INVOLVED_IN_REGULATION_OF = "involved_in_regulation_of"
TYPE_GENE = "gene"
TYPE_GOTERM = "goterm"
TYPE_PATHWAY = "pathway"
TYPE_PUBLICATION = "publication"

categories = [TYPE_GENE, TYPE_PUBLICATION, TYPE_PATHWAY, TYPE_GOTERM]
USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")


class RelationshipType(str, Enum):
    INVOLVED_IN = INVOLVED_IN
    ACTS_UPSTREAM_OF_OR_WITHIN = ACTS_UPSTREAM_OF_OR_WITHIN
    INVOLVED_IN_REGULATION_OF = INVOLVED_IN_REGULATION_OF


router = APIRouter()


@router.get("/api/bioentity/{id}", tags=["bioentity"])
async def get_bioentity_by_id(
    id: str = Query(
        ...,
        description="example: `CURIE identifier of a bioentity (e.g. a gene) "
        "(e.g. ZFIN:ZDB-GENE-990415-1)`",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Get bioentities by their ids (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)
    """

    # special case MGI, sigh
    if id.startswith("MGI:"):
        id = id.replace("MGI:", "MGI:MGI:")

    # fields is translated to fl in solr, which determines which stored fields should be returned with
    # the query
    fields = "id,bioentity_name,synonym,taxon,taxon_label"

    # query_filters is translated to the qf solr parameter
    # boost fields %5E2 -> ^2, %5E1 -> ^1
    query_filters = "bioentity%5E2"
    log.info(id)

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows)
    # id here is passed to solr q parameter, query_filters go to the boost, fields are what's returned
    bioentity = run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.BIOENTITY, id, query_filters, fields, optionals
    )
    return bioentity


@router.get("/api/bioentity/function/{id}", tags=["bioentity"])
async def get_annotations_by_goterm_id(
    id: str = Query(
        ...,
        description="example: `CURIE identifier of a function term "
        "(e.g. GO:0044598)`",
    ),
    evidence: List[str] = Query(None),
    start: int = 0,
    rows: int = 100,
):
    """
    Returns annotations using the provided GO term, (e.g. GO:0044598)
    """

    # dictates the fields to return, annotation_class,aspect
    fields = (
        "date,assigned_by,bioentity_label,bioentity_name,synonym,taxon,"
        "taxon_label,panther_family,panther_family_label,evidence,evidence_type,"
        "reference,annotation_extension_class,annotation_extension_class_label"
    )

    # boost fields %5E2 -> ^2, %5E1 -> ^1
    query_filters = (
        "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf="
        "bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf="
        "annotation_extension_class%5E2&qf=annotation_extension_class_label_searchable%5E1&qf="
        "reference_searchable%5E1&qf=panther_family_searchable%5E1&qf="
        "panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"
    )

    evidences = evidence
    evidence = ""
    if evidences is not None:
        evidence = "&fq=evidence_closure:("
        for ev in evidences:
            evidence += '"' + ev + '",'
        evidence = evidence[:-1]
        evidence += ")"

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows) + evidence
    data = run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals
    )

    return data


@router.get("/api/bioentity/function/{id}/genes", tags=["bioentity"])
async def get_genes_by_goterm_id(
    id: str = Query(..., description="CURIE identifier of a GO term"),
    taxon: List[str] = Query(
        default=None,
        description="One or more taxon CURIE to filter "
        "associations by subject taxon",
    ),
    relationship_type: RelationshipType = Query(
        default=RelationshipType.INVOLVED_IN,
        description="relationship type ('involved_in’,"
        "‘involved_in_regulation_of’ or "
        "‘acts_upstream_of_or_within’),",
    ),
    relation: str = Query(None, description="A relation CURIE to filter associations"),
    slim: List[str] = Query(
        default=None,
        description="Map objects up slim to a higher level"
        " category. Value can be ontology "
        "class ID or subset ID",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Returns genes annotated to the provided GO Term, (e.g. GO:0044598)
    """
    if relationship_type == ACTS_UPSTREAM_OF_OR_WITHIN:
        return search_associations(
            subject_category="gene",
            object_category="function",
            fq={
                "regulates_closure": id,
            },
            subject_taxon=taxon,
            invert_subject_object=True,
            user_agent=USER_AGENT,
            slim=slim,
            taxon=taxon,
            relation=relation,
            url=ESOLR.GOLR,
            start=start,
            rows=rows,
        )
    elif relationship_type == INVOLVED_IN_REGULATION_OF:
        # Temporary fix until https://github.com/geneontology/amigo/pull/469
        # and https://github.com/owlcollab/owltools/issues/241 are resolved
        return search_associations(
            subject_category="gene",
            object_category="function",
            fq={
                "regulates_closure": id,
                "-isa_partof_closure": id,
            },
            subject_taxon=taxon,
            invert_subject_object=True,
            user_agent=USER_AGENT,
            taxon=taxon,
            slim=slim,
            relation=relation,
            url=ESOLR.GOLR,
            start=start,
            rows=rows,
        )
    elif relationship_type == INVOLVED_IN:
        return search_associations(
            subject_category="gene",
            object_category="function",
            subject=id,
            subject_taxon=taxon,
            invert_subject_object=True,
            taxon=taxon,
            user_agent=USER_AGENT,
            url=ESOLR.GOLR,
        )


@router.get("/api/bioentity/function/{id}/taxons", tags=["bioentity"])
async def get_taxon_by_goterm_id(
    id: str = Query(..., description="CURIE identifier of a GO term, e.g. GO:0044598"),
    evidence: List[str] = Query(
        default=None,
        description="Object id, e.g. ECO:0000501 (for IEA; "
        "Includes inferred by default) or a "
        "specific publication or other supporting "
        "object, e.g. ZFIN:ZDB-PUB-060503-2",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Returns taxon information for genes annotated to the provided GO term (e.g. GO:0044598)
    """

    fields = "taxon,taxon_label"
    query_filters = "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf=bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf=annotation_extension_class%5E2&qf=annotation_extension_class_label_searchable%5E1&qf=reference_searchable%5E1&qf=panther_family_searchable%5E1&qf=panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"

    evidences = evidence
    evidence = ""
    if evidences is not None:
        evidence = "&fq=evidence_closure:("
        for ev in evidences:
            evidence += '"' + ev + '",'
        evidence = evidence[:-1]
        evidence += ")"

    taxon_restrictions = ""
    cfg = get_config()
    if cfg.taxon_restriction is not None:
        taxon_restrictions = "&fq=taxon_subset_closure:("
        for c in cfg.taxon_restriction:
            taxon_restrictions += '"' + c + '",'
        taxon_restrictions = taxon_restrictions[:-1]
        taxon_restrictions += ")"

    optionals = (
        "&defType=edismax&start="
        + str(start)
        + "&rows="
        + str(rows)
        + evidence
        + taxon_restrictions
    )
    data = run_solr_text_on(
        ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals
    )

    return data


@router.get("/api/bioentity/gene/{id}/function", tags=["bioentity"])
async def get_annotations_by_gene_id(
    id: str = Query(..., description="CURIE identifier of a GO term, e.g. GO:0044598"),
    # ... in query means "required" parameter.
    slim: List[str] = Query(
        default=None,
        description="Map objects up slim to a higher level"
        " category. Value can be ontology "
        "class ID or subset ID",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Returns GO terms associated to a gene. (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)

    IMPLEMENTATION DETAILS
    ----------------------

    Note: currently this is implemented as a query to the GO/AmiGO solr instance.
    This directly supports IDs such as:

     - ZFIN e.g. ZFIN:ZDB-GENE-050417-357

    Note that the AmiGO GOlr natively stores MGI annotations to MGI:MGI:nn. However,
    the standard for biolink is MGI:nnnn, so you should use this (will be transparently
    mapped to legacy ID)

    Additionally, for some species such as Human, GO has the annotation attached to the UniProt ID.
    Again, this should be transparently handled; e.g. you can use NCBIGene:6469, and this will be
    mapped behind the scenes for querying.
    """

    assocs = search_associations(
        object_category="function",
        subject_category="gene",
        subject=id,
        user_agent=USER_AGENT,
        url=ESOLR.GOLR,
        start=start,
        rows=rows,
        slim=slim,
    )
    log.info("should be null assocs")
    log.info(assocs)
    # If there are no associations for the given ID, try other IDs.
    # Note the AmiGO instance does *not* support equivalent IDs
    if len(assocs["associations"]) == 0:
        # Note that GO currently uses UniProt as primary ID for some
        # sources: https://github.com/biolink/biolink-api/issues/66
        # https://github.com/monarch-initiative/dipper/issues/461
        # prots = scigraph.gene_to_uniprot_proteins(id)
        prots = gene_to_uniprot_from_mygene(id)
        for prot in prots:
            pr_assocs = search_associations(
                object_category="function",
                subject=prot,
                user_agent=USER_AGENT,
                url=ESOLR.GOLR,
                start=start,
                rows=rows,
                slim=slim,
            )
            num_found = pr_assocs.get("numFound")
            if num_found > 0:
                num_found = num_found + pr_assocs.get("numFound")
            assocs["numFound"] = num_found
            for asc in pr_assocs["associations"]:
                log.info(asc)
                assocs["associations"].append(asc)
    return assocs


@router.get("/api/gp/{id}/models", tags=["bioentity"])
async def get_gocams_by_geneproduct_id(
    id: str = Query(
        None,
        description="A Gene Product CURIE (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)",
    )
):
    """
    Returns GO-CAM models associated with a given Gene Product identifier (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1)
    """
    # special case MGI, sigh
    if id.startswith("MGI:"):
        id = id.replace("MGI:", "MGI:MGI:")

    ns = Namespaces()
    ns.add_prefixmap("go")
    ont_r = OntologyResource(url="http://rdf.geneontology.org/sparql")
    si = SparqlImplementation(ont_r)
    # reformat curie into an identifiers.org URI
    id = "http://identifiers.org/" + id.split(":")[0].lower() + "/" + id
    log.info(
        "reformatted curie into IRI using identifiers.org from api/gp/{id}/models endpoint",
        id,
    )
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
        
        SELECT distinct ?gocam ?title
        
        WHERE 
        {
        
          GRAPH ?gocam {
            ?gocam metago:graphType metago:noctuaCam .    
            ?s enabled_by: ?gpnode .    
            ?gpnode rdf:type ?identifier .
            ?gocam dc:title ?title .   
            FILTER(?identifier = <%s>) .            
          }
        
        }
        ORDER BY ?gocam
        
    """
        % id
    )
    results = si._query(query)
    collated_results = []
    collated = {}
    for row in results:
        collated["gocam"] = row["gocam"].get("value")
        collated["title"] = row["title"].get("value")
        collated_results.append(collated)
    return collated_results
