import logging
from typing import List
from fastapi import APIRouter, Query
from ontobio.golr.golr_associations import search_associations
from .slimmer import gene_to_uniprot_from_mygene
from ontobio.util.user_agent import get_user_agent
from ontobio.golr.golr_query import run_solr_text_on, ESOLR, ESOLRDoc
from ontobio.config import get_config

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

router = APIRouter()

#core_parser_with_relation_filter.add_argument('relation', help='A relation CURIE to filter associations', default=None)

#core_parser_with_filters.add_argument('taxon', action='append',
                                      #help='One or more taxon CURIE to filter associations by subject taxon')
#core_parser_with_filters.add_argument('relation', help='A relation CURIE to filter associations', default=None)


@router.post("/bioentity/function/{id}", tags=["bioentity"])
async def get_function_associations(id: str, evidence: List[str] = Query(None), start: int = 0, rows: int = 100,
                                    facet: bool = Query(False, include_in_schema=False),
                                    unselect_evidence: bool = Query(False, include_in_schema=False),
                                    exclude_automatic_assertions: bool = Query(False, include_in_schema=False),
                                    fetch_objects: bool = Query(False, include_in_schema=False),
                                    use_compact_associations: bool = Query(False, include_in_schema=False),
                                    slim: bool = Query(False, include_in_schema=False)):
        """
        Returns annotations associated to a GO term
        """

        # annotation_class,aspect
        fields = "date,assigned_by,bioentity_label,bioentity_name,synonym,taxon," \
                 "taxon_label,panther_family,panther_family_label,evidence,evidence_type," \
                 "reference,annotation_extension_class,annotation_extension_class_label"
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


@router.post("/bioentity/function/{id}/genes", tags=["bioentity"])
async def get_function_by_id(id: str, evidence: List[str] = Query(None),
                             facet: bool = Query(False, include_in_schema=False),
                             unselect_evidence: bool = Query(False, include_in_schema=False),
                             exclude_automatic_assertions: bool = Query(False, include_in_schema=False),
                             fetch_objects: bool = Query(False, include_in_schema=False),
                             use_compact_associations: bool = Query(False, include_in_schema=False),
                             slim: bool = Query(False, include_in_schema=False),
                             start: int = 0, rows: int = 100):

    assocs = search_associations(
        object_category='function',
        subject_category='gene',
        subject=id,
        sort="id asc",
        user_agent=USER_AGENT,
        url="http://golr-aux.geneontology.io/solr",
        unselect_evidence=unselect_evidence,
        facet=facet,
        fetch_objects=fetch_objects,
        exclude_automatic_assertions=exclude_automatic_assertions,
        use_compact_associations=use_compact_associations,
        slim=slim,
        start=start,
        rows=rows,
        evidence=evidence

    )

    # If there are no associations for the given ID, try other IDs.
    # Note the AmiGO instance does *not* support equivalent IDs
    if len(assocs['associations']) == 0:
        # Note that GO currently uses UniProt as primary ID for some sources: https://github.com/biolink/biolink-api/issues/66
        # https://github.com/monarch-initiative/dipper/issues/461
        # prots = scigraph.gene_to_uniprot_proteins(id)
        prots = gene_to_uniprot_from_mygene(id)
        for prot in prots:
            pr_assocs = search_associations(
                subject_category='gene',
                object_category='function',
                subject=prot,
                sort="id asc",
                user_agent=USER_AGENT,
                url="http://golr-aux.geneontology.io/solr",
                unselect_evidence=unselect_evidence,
                facet=facet,
                fetch_objects=fetch_objects,
                exclude_automatic_assertions=exclude_automatic_assertions,
                use_compact_associations=use_compact_associations,
                slim=slim,
                start=start,
                rows=rows
            )
            assocs = pr_assocs
    return assocs

