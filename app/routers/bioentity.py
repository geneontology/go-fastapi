import logging
from typing import List
from fastapi import APIRouter, Query
from ontobio.golr.golr_associations import search_associations
from .slimmer import gene_to_uniprot_from_mygene
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import run_solr_text_on, ESOLR, ESOLRDoc
from ontobio.config import get_config
from enum import Enum
from pprint import pprint

# TODO: @api.marshal_with(association_results)
log = logging.getLogger(__name__)

INVOLVED_IN = 'involved_in'
ACTS_UPSTREAM_OF_OR_WITHIN = 'acts_upstream_of_or_within'
FUNCTION_CATEGORY = 'function'
ANATOMY_CATEGORY = 'anatomy'
INVOLVED_IN_REGULATION_OF = 'involved_in_regulation_of'
TYPE_GENE = 'gene'
TYPE_GOTERM = 'goterm'
TYPE_PATHWAY = 'pathway'
TYPE_PUBLICATION = 'publication'

categories = [TYPE_GENE, TYPE_PUBLICATION, TYPE_PATHWAY, TYPE_GOTERM]
USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")


class RelationshipType(str, Enum):
    INVOLVED_IN = INVOLVED_IN
    ACTS_UPSTREAM_OF_OR_WITHIN = ACTS_UPSTREAM_OF_OR_WITHIN
    INVOLVED_IN_REGULATION_OF = INVOLVED_IN_REGULATION_OF


router = APIRouter()


@router.get("/bioentity/function/{id}", tags=["bioentity"])
async def get_annotations_by_goterm_id(id: str = Query(..., description="example: `CURIE identifier of a function term "
                                                                        "(e.g. GO:0044598)`"),
                                     evidence: List[str] = Query(None), start: int = 0, rows: int = 100):
    """
    Returns annotations associated to a GO term
    """

    # annotation_class,aspect
    fields = "date,assigned_by,bioentity_label,bioentity_name,synonym,taxon," \
             "taxon_label,panther_family,panther_family_label,evidence,evidence_type," \
             "reference,annotation_extension_class,annotation_extension_class_label"

    query_filters = "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf=" \
                    "bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf=" \
                    "annotation_extension_class%5E2&qf=annotation_extension_class_label_searchable%5E1&qf=" \
                    "reference_searchable%5E1&qf=panther_family_searchable%5E1&qf=" \
                    "panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"

    evidences = evidence
    evidence = ""
    if evidences is not None:
        evidence = "&fq=evidence_closure:("
        for ev in evidences:
            evidence += "\"" + ev + "\","
        evidence = evidence[:-1]
        evidence += ")"

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows) + evidence
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals)

    return data


@router.get("/bioentity/function/{id}/genes", tags=["bioentity"])
async def get_genes_by_goterm_id(id: str = Query(..., description="CURIE identifier of a GO term"),
                                 taxon: List[str] = Query(default=None, description="One or more taxon CURIE to filter "
                                                                                    "associations by subject taxon"),
                                 relationship_type: RelationshipType = Query(default=RelationshipType.INVOLVED_IN,
                                                                             description="relationship type ('involved_in’,"
                                                                                         "‘involved_in_regulation_of’ or "
                                                                                         "‘acts_upstream_of_or_within’),"),
                                 relation: str = Query(None, description="A relation CURIE to filter associations"),
                                 slim: List[str] = Query(default=None,
                                                         description="Map objects up slim to a higher level"
                                                                     " category. Value can be ontology "
                                                                     "class ID or subset ID"),
                                 evidence: List[str] = Query(default=None),
                                 start: int = 0, rows: int = 100):

        """
        Returns genes associated to a GO term
        """
        if relationship_type == ACTS_UPSTREAM_OF_OR_WITHIN:
            return search_associations(
                subject_category='gene',
                object_category='function',
                fq={
                    'regulates_closure': id,
                },
                subject_taxon=taxon,
                invert_subject_object=True,
                user_agent=USER_AGENT,
                slim=slim,
                taxon=taxon,
                relation=relation,
                url="http://golr-aux.geneontology.io/solr"
            )
        elif relationship_type == INVOLVED_IN_REGULATION_OF:
            # Temporary fix until https://github.com/geneontology/amigo/pull/469
            # and https://github.com/owlcollab/owltools/issues/241 are resolved
            return search_associations(
                subject_category='gene',
                object_category='function',
                fq={
                    'regulates_closure': id,
                    '-isa_partof_closure': id,
                },
                subject_taxon=taxon,
                invert_subject_object=True,
                user_agent=USER_AGENT,
                slim=slim,
                relation=relation,
                url="http://golr-aux.geneontology.io/solr"
            )
        elif relationship_type == INVOLVED_IN:
            return search_associations(
                subject_category='gene',
                object_category='function',
                subject=id,
                subject_taxon=taxon,
                invert_subject_object=True,
                user_agent=USER_AGENT,
                url="http://golr-aux.geneontology.io/solr"
            )


@router.get("/bioentity/function/{id}/taxons", tags=["bioentity"])
async def get_taxon_by_goterm_id(id: str = Query(..., description="CURIE identifier of a GO term, e.g. GO:0044598"),
                                   evidence: List[str] = Query(default=None,
                                                               description="Object id, e.g. ECO:0000501 (for IEA; "
                                                                           "Includes inferred by default) or a "
                                                                           "specific publication or other supporting "
                                                                           "object, e.g. ZFIN:ZDB-PUB-060503-2"),
                                   start: int = 0, rows: int = 100,
                                   facet: bool = Query(False, include_in_schema=False),
                                   unselect_evidence: bool = Query(False, include_in_schema=False),
                                   exclude_automatic_assertions: bool = Query(False, include_in_schema=False),
                                   fetch_objects: bool = Query(False, include_in_schema=False),
                                   use_compact_associations: bool = Query(False, include_in_schema=False)
                                   ):
    """
    Returns taxons associated to a GO term
    """

    fields = "taxon,taxon_label"
    query_filters = "annotation_class%5E2&qf=annotation_class_label_searchable%5E1&qf=bioentity%5E2&qf=bioentity_label_searchable%5E1&qf=bioentity_name_searchable%5E1&qf=annotation_extension_class%5E2&qf=annotation_extension_class_label_searchable%5E1&qf=reference_searchable%5E1&qf=panther_family_searchable%5E1&qf=panther_family_label_searchable%5E1&qf=bioentity_isoform%5E1"

    evidences = evidence
    evidence = ""
    if evidences is not None:
        evidence = "&fq=evidence_closure:("
        for ev in evidences:
            evidence += "\"" + ev + "\","
        evidence = evidence[:-1]
        evidence += ")"

    taxon_restrictions = ""
    cfg = get_config()
    if cfg.taxon_restriction is not None:
        taxon_restrictions = "&fq=taxon_subset_closure:("
        for c in cfg.taxon_restriction:
            taxon_restrictions += "\"" + c + "\","
        taxon_restrictions = taxon_restrictions[:-1]
        taxon_restrictions += ")"

    optionals = "&defType=edismax&start=" + str(start) + "&rows=" + str(rows) + evidence + taxon_restrictions
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ANNOTATION, id, query_filters, fields, optionals)

    return data


@router.get("/bioentity/gene/{id}/function", tags=["bioentity"])
async def get_annotations_by_gene_id(id: str = Query(..., description="CURIE identifier of a GO term, e.g. GO:0044598"),
                             # ... in query means "required" parameter.
                             slim: List[str] = Query(default=None, description="Map objects up slim to a higher level"
                                                                               " category. Value can be ontology "
                                                                               "class ID or subset ID"),

                             start: int = 0, rows: int = 100):
    """
    Returns GO terms associated to a gene.

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
        object_category='function',
        subject_category='gene',
        subject=id,
        sort="id asc",
        user_agent=USER_AGENT,
        url="http://golr-aux.geneontology.io/solr",
        start=start,
        rows=rows,
        slim=slim
    )

    # If there are no associations for the given ID, try other IDs.
    # Note the AmiGO instance does *not* support equivalent IDs
    if len(assocs['associations']) == 0:
        # Note that GO currently uses UniProt as primary ID for some sources: https://github.com/biolink/biolink-api/issues/66
        # https://github.com/monarch-initiative/dipper/issues/461
        # prots = scigraph.gene_to_uniprot_proteins(id)
        prots = gene_to_uniprot_from_mygene(id)
        prot_associations = []
        num_found = 0
        for prot in prots:
            pr_assocs = search_associations(
                subject_category='gene',
                object_category='function',
                subject=prot,
                sort="id asc",
                user_agent=USER_AGENT,
                url="http://golr-aux.geneontology.io/solr",
                start=start,
                rows=rows
            )
            if pr_assocs.get('numFound') > 0:
                prot_associations.append(pr_assocs.get('associations'))
                num_found = num_found + pr_assocs.get('numFound')
            assocs['associations'] = prot_associations
            # TODO need to filter out duplicates
            assocs['numFound'] = num_found
    return assocs
