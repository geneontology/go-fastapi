import logging
from enum import Enum
from typing import List

from fastapi import APIRouter, Query
from ontobio.config import get_config
from ontobio.golr.golr_associations import search_associations

from app.utils.golr.golr_utils import run_solr_text_on
from app.utils.settings import ESOLR, ESOLRDoc, get_user_agent

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
USER_AGENT = get_user_agent()


class RelationshipType(str, Enum):
    INVOLVED_IN = INVOLVED_IN
    ACTS_UPSTREAM_OF_OR_WITHIN = ACTS_UPSTREAM_OF_OR_WITHIN
    INVOLVED_IN_REGULATION_OF = INVOLVED_IN_REGULATION_OF


router = APIRouter()


@router.get("/api/bioentity/{id}", tags=["bioentity"])
async def get_bioentity_by_id(
    id: str = Query(
        ...,
        description="example: `CURIE identifier of a bioentity (e.g. a gene) " "(e.g. ZFIN:ZDB-GENE-990415-1, )`",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Get bio-entities by their identifiers.

    Retrieves bio-entities (e.g., genes) based on their identifiers in CURIE format.

    :param id: The CURIE identifier of the bioentity to be retrieved. (required)
    :param start: The starting index for pagination. Default is 0. (optional)
    :param rows: The number of results per page. Default is 100. (optional)

    :return: A dictionary containing the bioentity information retrieved from the database.
             The dictionary will contain fields such as 'id', 'bioentity_name', 'synonym', 'taxon',
             and 'taxon_label' associated with the specified bioentity.

    :raises HTTPException: If the bioentity with the provided identifier is not found in the database.

    :note:
        - For example, to get a gene with the identifier 'ZFIN:ZDB-GENE-990415-1', the URL should be:
          '/api/bioentity/ZFIN:ZDB-GENE-990415-1'.
        - The 'start' and 'rows' parameters can be used for pagination of results.
          'start' determines the starting index for fetching results, and 'rows' specifies
          the number of results to be retrieved per page.
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
    bioentity = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.BIOENTITY, id, query_filters, fields, optionals)
    return bioentity


@router.get("/api/bioentity/function/{id}", tags=["bioentity"])
async def get_annotations_by_goterm_id(
    id: str = Query(
        ...,
        description="example: `CURIE identifier of a function term " "(e.g. GO:0044598)`",
    ),
    evidence: List[str] = Query(None),
    start: int = 0,
    rows: int = 100,
):
    """Returns annotations using the provided GO term.

    Retrieves annotations based on the provided Gene Ontology (GO) term identifier.
    The GO term identifier should be represented in CURIE format (e.g., GO:0044598).

    :param id: The CURIE identifier of the GO term to be used for annotation retrieval. (required)
    :param evidence: List of evidence codes to filter the results. Default is None. (optional)
    :param start: The starting index for pagination. Default is 0. (optional)
    :param rows: The number of results per page. Default is 100. (optional)

    :return: A dictionary containing the annotation information retrieved from the database.
             The dictionary will contain fields such as 'date', 'assigned_by', 'bioentity_label',
             'bioentity_name', 'synonym', 'taxon', 'taxon_label', 'panther_family', 'panther_family_label',
             'evidence', 'evidence_type', 'reference', 'annotation_extension_class',
             and 'annotation_extension_class_label' associated with the provided GO term.

    :rtype: dict

    :note:
        - For example, to get annotations for the GO term 'GO:0044598', the URL should be:
          '/api/bioentity/function/GO:0044598'.
        - The 'evidence' parameter can be used to filter annotations by specific evidence codes.
        - The 'start' and 'rows' parameters can be used for pagination of results.
          'start' determines the starting index for fetching results, and 'rows' specifies
          the number of results to be retrieved per page.
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
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals)

    return data


@router.get("/api/bioentity/function/{id}/genes", tags=["bioentity"])
async def get_genes_by_goterm_id(
    id: str = Query(..., description="CURIE identifier of a GO term"),
    taxon: List[str] = Query(
        default=None,
        description="One or more taxon CURIE to filter " "associations by subject taxon",
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
        description="Map objects up slim to a higher level" " category. Value can be ontology " "class ID or subset ID",
    ),
    start: int = 0,
    rows: int = 100,
):
    """Returns genes annotated to the provided GO Term.

    Retrieves genes annotated to the provided Gene Ontology (GO) term. The GO term should be
    represented in CURIE format (e.g., GO:0044598).

    :param id: The CURIE identifier of the GO term to be used for gene retrieval. (required)
    :param taxon: One or more taxon CURIEs to filter associations by subject taxon. Default is None. (optional)
    :param relationship_type: Relationship type for filtering associations.
                              Options: 'involved_in', 'involved_in_regulation_of', or 'acts_upstream_of_or_within'.
                              Default is 'involved_in'. (optional)
    :param relation: A relation CURIE to filter associations. Default is None. (optional)
    :param slim: Map objects up slim to a higher-level category. Value can be an ontology class ID or subset ID.
                 Default is None. (optional)
    :param start: The starting index for pagination. Default is 0. (optional)
    :param rows: The number of results per page. Default is 100. (optional)

    :return: A dictionary containing the gene annotation information retrieved from the database.
             The dictionary will contain fields such as 'date', 'assigned_by', 'bioentity_label',
             'bioentity_name', 'synonym', 'taxon', 'taxon_label', 'panther_family', 'panther_family_label',
             'evidence', 'evidence_type', 'reference', 'annotation_extension_class',
             and 'annotation_extension_class_label' associated with the provided GO term.

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
    """Returns taxon information for genes annotated to the provided GO term.

    Retrieves taxon information for genes annotated to the provided Gene Ontology (GO) term.
    The GO term should be represented in CURIE format (e.g., GO:0044598).

    :param id: The CURIE identifier of the GO term to be used for taxon retrieval. (required)
    :param evidence: List of object ids used for evidence filtering.
                     Example: ['ECO:0000501', 'ZFIN:ZDB-PUB-060503-2']. Default is None. (optional)
    :param start: The starting index for pagination. Default is 0. (optional)
    :param rows: The number of results per page. Default is 100. (optional)

    :return: A dictionary containing the taxon information for genes annotated to the provided GO term.
             The dictionary will contain fields such as 'taxon' and 'taxon_label' associated with the genes.
    """
    fields = "taxon,taxon_label"
    query_filters = (
        "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf="
        "bioentity%5E2&qf=bioentity_label_searchable%5E1&qf="
        "bioentity_name_searchable%5E1&qf=annotation_extension_class%5E2&qf="
        "annotation_extension_class_label_searchable%5E1&qf=reference_searchable%5E1&qf="
        "panther_family_searchable%5E1&qf=panther_family_label_searchable%5E1&qf="
        "bioentity_isoform%5E1"
    )

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

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows) + evidence + taxon_restrictions
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals)

    return data


@router.get("/api/bioentity/gene/{id}/function", tags=["bioentity"])
async def get_annotations_by_gene_id(
    id: str = Query(..., description="CURIE identifier of a GO term, e.g. ZFIN:ZDB-GENE-050417-357"),
    # ... in query means "required" parameter.
    slim: List[str] = Query(
        default=None,
        description="Map objects up slim to a higher level" " category. Value can be ontology " "class ID or subset ID",
    ),
    start: int = 0,
    rows: int = 100,
):
    """
    Returns GO terms associated with a gene.

    Retrieves Gene Ontology (GO) terms associated with a gene identified by its CURIE identifier.
    The gene identifier should be represented in CURIE format (e.g., ZFIN:ZDB-GENE-050417-357).

    :param id: The CURIE identifier of the gene for which GO term associations are retrieved. (required)
    :param slim: Map objects up slim to a higher-level category. Value can be an ontology class ID or subset ID.
                 Default is None. (optional)
    :param start: The starting index for pagination. Default is 0. (optional)
    :param rows: The number of results per page. Default is 100. (optional)

    :return: A dictionary containing the GO term associations for the provided gene.
             The dictionary will contain fields such as 'numFound' and 'associations' associated with the gene.

    IMPLEMENTATION DETAILS
    ----------------------

    Note: This method is implemented as a query to the GO/AmiGO Solr instance. The supported gene IDs include:

     - ZFIN (e.g., ZFIN:ZDB-GENE-050417-357)

    Note that the AmiGO GOlr natively stores MGI annotations to MGI:MGI:nn. However, the standard for biolink is MGI:nnnn,
    so you should use this (will be transparently mapped to legacy ID).

    Additionally, for some species such as Human, GO has the annotation attached to the UniProt ID.
    Again, this should be transparently handled; e.g., you can use NCBIGene:6469, and this will be mapped behind the scenes for querying.
    """
    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")

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
