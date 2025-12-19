"""slimmer router."""

import logging
from enum import Enum
from typing import List

from fastapi import APIRouter, Query

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.golr_wrappers import map2slim
from app.utils.mygene_utils import gene_to_uniprot_from_mygene, uniprot_to_gene_from_mygene
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
        examples=["ZFIN:ZDB-GENE-980526-388", "MGI:3588192"],
    ),
    slim: List[str] = Query(
        ...,
        description="a set of GO term ids to use as the slim, example: GO:0008150, GO:0003674, GO:0005575",
        examples=["GO:0008150", "GO:0003674", "GO:0005575"],
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
        elif "MGI:" in s:
            # GOLr expects MGI identifiers in MGI:MGI: format
            if not s.startswith("MGI:MGI:"):
                slimmer_subjects.append(s.replace("MGI:", "MGI:MGI:"))
            else:
                slimmer_subjects.append(s)
        elif "WormBase:" in s:
            slimmer_subjects.append(s.replace("WormBase:", "WB:"))
        else:
            slimmer_subjects.append(s)

    # Create mapping from converted subjects back to original subjects
    subject_mapping = {}
    for _i, original_subject in enumerate(subject):
        if "HGNC:" in original_subject or "NCBIGene:" in original_subject or "ENSEMBL:" in original_subject:
            # These were converted to UniProt IDs
            prots = gene_to_uniprot_from_mygene(original_subject)
            if len(prots) == 0:
                subject_mapping[original_subject] = original_subject
            else:
                for prot in prots:
                    subject_mapping[prot] = original_subject
        elif "MGI:" in original_subject:
            # We converted MGI: to MGI:MGI: for GOLr
            if not original_subject.startswith("MGI:MGI:"):
                converted = original_subject.replace("MGI:", "MGI:MGI:")
                subject_mapping[converted] = original_subject
            else:
                subject_mapping[original_subject] = original_subject
        elif "WormBase:" in original_subject:
            converted = original_subject.replace("WormBase:", "WB:")
            subject_mapping[converted] = original_subject
        else:
            subject_mapping[original_subject] = original_subject

    # Log the converted subjects
    logger.info(f"Original subjects: {subject}")
    logger.info(f"Converted subjects for GOLr: {slimmer_subjects}")

    # Use ontobio map2slim with rate limiting and retry logic from golr_wrappers
    results = map2slim(
        subjects=slimmer_subjects,
        slim=slim,
        object_category="function",
        user_agent=USER_AGENT,
        url=ESOLR.GOLR.value,
        relationship_type=relationship_type.value,
        exclude_automatic_assertions=exclude_automatic_assertions,
        rows=rows,
        start=start,
    )

    # Map subjects back to original IDs in results
    for result in results:
        if result["subject"] in subject_mapping:
            result["subject"] = subject_mapping[result["subject"]]

        # Also map the subject IDs within associations
        for association in result.get("assocs", []):
            if association["subject"]["id"] in subject_mapping:
                association["subject"]["id"] = subject_mapping[association["subject"]["id"]]

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
        logger.warning(f"No slim results found for subjects: {slimmer_subjects}")
        raise DataNotFoundException(detail="No results found")
    return results


