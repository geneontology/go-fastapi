import logging
from typing import List

from ontobio.golr.golr_associations import map2slim
from biothings_client import get_client
from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent
from enum import Enum

INVOLVED_IN = 'involved_in'
ACTS_UPSTREAM_OF_OR_WITHIN = 'acts_upstream_of_or_within'
FUNCTION_CATEGORY = 'function'
ANATOMY_CATEGORY = 'anatomy'
USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")

router = APIRouter()


class RelationshipType(str, Enum):
    acts_upstream_of_or_within = ACTS_UPSTREAM_OF_OR_WITHIN,
    involved_in = INVOLVED_IN


@router.get("/bioentityset/slimmer/function", tags=["bioentityset/slimmer"])
async def slimmer_function(relationship_type: RelationshipType =
                           Query(default=RelationshipType.acts_upstream_of_or_within),
                           subject: List[str] = Query(..., description="example: ZFIN:ZDB-GENE-980526-388"),
                           slim: List[str] = Query(..., description="Map objects up (slim) to a higher level category. "
                                                                    "Value can be ontology class ID, "
                                                                    "example: GO:0005575"),
                           exclude_automatic_assertions: bool = False,
                           rows: int = 100, start: int = 1):
    """
    For a given gene(s), summarize its annotations over a defined set of slim
    """

    # Note that GO currently uses UniProt as primary ID
    # for some sources: https://github.com/biolink/biolink-api/issues/66
    # https://github.com/monarch-initiative/dipper/issues/461

    # TODO - figure out if this is still needed. WormBase to WB
    subjects = [x.replace('WormBase:', 'WB:') if 'WormBase:' in x else x for x in subject]
    slimmer_subjects = []
    for s in subjects:
        if 'HGNC:' in s or 'NCBIGene:' in s or 'ENSEMBL:' in s:
            prots = gene_to_uniprot_from_mygene(s)
            if len(prots) == 0:
                prots = [s]
            slimmer_subjects += prots
        else:
            slimmer_subjects.append(s)

    results = map2slim(
        subjects=slimmer_subjects,
        slim=slim,
        object_category='function',
        user_agent=USER_AGENT,
        url="http://golr-aux.geneontology.io/solr"
    )

    # To the fullest extent possible return HGNC ids
    checked = {}
    for result in results:
        for association in result['assocs']:
            taxon = association['subject']['taxon']['id']
            protein_id = association['subject']['id']
            if taxon == 'NCBITaxon:9606' and protein_id.startswith('UniProtKB:'):
                if protein_id not in checked:
                    genes = uniprot_to_gene_from_mygene(protein_id)
                    for gene in genes:
                        if gene.startswith('HGNC'):
                            association['subject']['id'] = gene
                            checked[protein_id] = gene
                else:
                    association['subject']['id'] = checked[protein_id]

    return results


def gene_to_uniprot_from_mygene(id):
    """
    Query MyGeneInfo with a gene and get its corresponding UniProt ID
    """
    uniprot_ids = []
    mg = get_client('gene')
    if id.startswith('NCBIGene:'):
        # MyGeneInfo uses 'entrezgene' prefix instead of 'NCBIGene'
        id = id.replace('NCBIGene', 'entrezgene')
    try:
        results = mg.query(id, fields='uniprot')
        print("results from mygene for ", id, ": ", results)
        if results['hits']:
            for hit in results['hits']:
                if 'uniprot' not in hit:
                    continue
                if 'Swiss-Prot' in hit['uniprot']:
                    uniprot_id = hit['uniprot']['Swiss-Prot']
                    if isinstance(uniprot_id, str):
                        if not uniprot_id.startswith('UniProtKB'):
                            uniprot_id = "UniProtKB:{}".format(uniprot_id)
                        uniprot_ids.append(uniprot_id)
                    else:
                        for x in uniprot_id:
                            if not x.startswith('UniProtKB'):
                                x = "UniProtKB:{}".format(x)
                            uniprot_ids.append(x)
                else:
                    trembl_ids = hit['uniprot']['TrEMBL']
                    for x in trembl_ids:
                        if not x.startswith('UniProtKB'):
                            x = "UniProtKB:{}".format(x)
                        uniprot_ids.append(x)
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))

    return uniprot_ids


def uniprot_to_gene_from_mygene(id):
    """
    Query MyGeneInfo with a UniProtKB id and get its corresponding HGNC gene
    """
    gene_id = None
    if id.startswith('UniProtKB'):
        id = id.split(':', 1)[1]

    mg = get_client('gene')
    try:
        results = mg.query(id, fields='HGNC')
        if results['hits']:
            hit = results['hits'][0]
            gene_id = hit['HGNC']
            if not gene_id.startswith('HGNC'):
                gene_id = 'HGNC:{}'.format(gene_id)
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))

    return [gene_id]
