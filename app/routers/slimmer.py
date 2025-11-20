"""slimmer router."""

import logging
from enum import Enum
from typing import List

from biothings_client import get_client
from fastapi import APIRouter, Query
from ontobio.golr.golr_associations import map2slim

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.settings import ESOLR, get_user_agent

INVOLVED_IN = "involved_in"
ACTS_UPSTREAM_OF_OR_WITHIN = "acts_upstream_of_or_within"
FUNCTION_CATEGORY = "function"
ANATOMY_CATEGORY = "anatomy"
USER_AGENT = get_user_agent()

router = APIRouter()
logger = logging.getLogger()


class RelationshipType(str, Enum):

    """Relationship type for slimmer."""

    acts_upstream_of_or_within = ACTS_UPSTREAM_OF_OR_WITHIN
    involved_in = INVOLVED_IN


@router.get(
    "/api/bioentityset/slimmer/function",
    tags=["bioentityset/slimmer"],
    description="For a given gene(s), summarize its annotations over a defined set of slim.",
)
async def slimmer_function(
    relationship_type: RelationshipType = Query(default=RelationshipType.acts_upstream_of_or_within),
    subject: List[str] = Query(
        ...,
        description="example: ZFIN:ZDB-GENE-980526-388, MGI:3588192",
        example=["ZFIN:ZDB-GENE-980526-388", "MGI:3588192"],
    ),
    slim: List[str] = Query(
        ...,
        description="a set of GO term ids to use as the slim, example: GO:0008150, GO:0003674, GO:0005575",
        example=["GO:0008150", "GO:0003674", "GO:0005575"],
    ),
    exclude_automatic_assertions: bool = False,
    rows: int = Query(default=-1, description="Number of rows to return, -1 for all"),
    start: int = Query(default=0, description="Row to start at"),
):
    """For a given gene(s), summarize its annotations over a defined set of slim."""
    # Note that GO currently uses UniProt as primary ID
    # for some sources: https://github.com/biolink/biolink-api/issues/66

    slimmer_subjects = []
    for s in subject:
        if "HGNC:" in s or "NCBIGene:" in s or "ENSEMBL:" in s:
            prots = gene_to_uniprot_from_mygene(s)
            if len(prots) == 0:
                prots = [s]
            slimmer_subjects += prots
        elif "MGI:MGI:" in s:
            slimmer_subjects.append(s.replace("MGI:MGI:", "MGI:"))
        elif "WormBase:" in s:
            slimmer_subjects.append(s.replace("WormBase:", "WB:"))
        else:
            slimmer_subjects.append(s)

    results = map2slim(
        subjects=slimmer_subjects,
        slim=slim,
        object_category="function",
        user_agent=USER_AGENT,
        url=ESOLR.GOLR,
        relationship_type=relationship_type.value,
        exclude_automatic_assertions=exclude_automatic_assertions,
        # rows=-1 sets row limit to 100000 (max_rows set in GolrQuery) and also iterates
        # through results via GolrQuery method.
        rows=rows,
        start=start,
    )

    # To the fullest extent possible return HGNC ids
    checked = {}
    for result in results:
        for association in result["assocs"]:
            taxon = association["subject"]["taxon"]["id"]
            protein_id = association["subject"]["id"]
            if taxon == "NCBITaxon:9606" and protein_id.startswith("UniProtKB:"):
                if protein_id not in checked:
                    try:
                        genes = uniprot_to_gene_from_mygene(protein_id)
                        found_hgnc = False
                        for gene in genes:
                            if gene.startswith("HGNC"):
                                association["subject"]["id"] = gene
                                checked[protein_id] = gene
                                found_hgnc = True
                                break
                        # If no HGNC ID was found in the results, keep the original UniProt ID
                        if not found_hgnc:
                            logger.info(f"No HGNC ID found in results for {protein_id}, keeping original")
                            checked[protein_id] = protein_id
                    except DataNotFoundException:
                        # If we can't map the UniProt back to HGNC, keep the UniProt ID
                        logger.warning("Could not map UniProt %s back to HGNC, keeping original ID", protein_id)
                        checked[protein_id] = protein_id
                else:
                    association["subject"]["id"] = checked[protein_id]
    if not results:
        raise DataNotFoundException(detail="No results found")
    return results


def gene_to_uniprot_from_mygene(id: str):
    """Query MyGeneInfo with a gene and get its corresponding UniProt ID."""
    uniprot_ids = []
    mg = get_client("gene")
    if id.startswith("NCBIGene:"):
        # MyGeneInfo uses 'entrezgene' prefix instead of 'NCBIGene'
        id = id.replace("NCBIGene", "entrezgene")
    try:
        results = mg.query(id, fields="uniprot")
        logger.info("results from mygene for %s: %s", id, results["hits"])
        if results["hits"]:
            for hit in results["hits"]:
                if "uniprot" not in hit:
                    continue
                if "Swiss-Prot" in hit["uniprot"]:
                    uniprot_id = hit["uniprot"]["Swiss-Prot"]
                    if isinstance(uniprot_id, str):
                        if not uniprot_id.startswith("UniProtKB"):
                            uniprot_id = "UniProtKB:{}".format(uniprot_id)
                        uniprot_ids.append(uniprot_id)
                    else:
                        for x in uniprot_id:
                            if not x.startswith("UniProtKB"):
                                x = "UniProtKB:{}".format(x)
                            uniprot_ids.append(x)
                else:
                    trembl_ids = hit["uniprot"]["TrEMBL"]
                    for x in trembl_ids:
                        if not x.startswith("UniProtKB"):
                            x = "UniProtKB:{}".format(x)
                        uniprot_ids.append(x)
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))
    if not uniprot_ids:
        raise DataNotFoundException(detail="No UniProtKB IDs found for {}".format(id))
    return uniprot_ids


def uniprot_to_gene_from_mygene(id: str):
    """Query MyGeneInfo with a UniProtKB id and get its corresponding HGNC gene."""
    gene_id = None
    if id.startswith("UniProtKB"):
        id = id.split(":", 1)[1]

    mg = get_client("gene")
    try:
        # Query specifically in the uniprot fields to avoid false matches
        results = mg.query(f"uniprot.Swiss-Prot:{id} OR uniprot.TrEMBL:{id}",
                          fields="HGNC,symbol,uniprot")
        if results["hits"]:
            # Verify the hit actually contains our UniProt ID
            for hit in results["hits"]:
                if "uniprot" in hit:
                    uniprot_data = hit["uniprot"]
                    # Check Swiss-Prot
                    has_id = False
                    if "Swiss-Prot" in uniprot_data:
                        swiss_prot = uniprot_data["Swiss-Prot"]
                        if (isinstance(swiss_prot, str) and swiss_prot == id) or \
                           (isinstance(swiss_prot, list) and id in swiss_prot):
                            has_id = True
                    # Check TrEMBL if not found
                    if not has_id and "TrEMBL" in uniprot_data:
                        trembl = uniprot_data["TrEMBL"]
                        if (isinstance(trembl, str) and trembl == id) or \
                           (isinstance(trembl, list) and id in trembl):
                            has_id = True

                    if has_id and "HGNC" in hit:
                        gene_id = hit["HGNC"]
                        if not gene_id.startswith("HGNC"):
                            gene_id = "HGNC:{}".format(gene_id)
                        break
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))

    if not gene_id:
        raise DataNotFoundException(detail="No HGNC IDs found for {}".format(id))
    return [gene_id]
