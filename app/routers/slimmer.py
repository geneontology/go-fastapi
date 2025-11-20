"""slimmer router."""

import logging
from enum import Enum
from typing import List

from fastapi import APIRouter, Query

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.golr_utils import gu_run_solr_text_on
from app.utils.mygene_utils import gene_to_uniprot_from_mygene, uniprot_to_gene_from_mygene
from app.utils.settings import ESOLR, ESOLRDoc, get_user_agent

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
    for i, original_subject in enumerate(subject):
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

    # Use local implementation to avoid timeout issues
    results = local_map2slim(
        subjects=slimmer_subjects,
        slim_terms=slim,
        relationship_type=relationship_type.value,
        exclude_automatic_assertions=exclude_automatic_assertions,
    )
    
    # Map subjects back to original IDs in results
    for result in results:
        if result["subject"] in subject_mapping:
            result["subject"] = subject_mapping[result["subject"]]

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


def local_map2slim(subjects, slim_terms,
                   relationship_type="acts_upstream_of_or_within",
                   exclude_automatic_assertions=False):
    """
    Local implementation of map2slim using gu_run_solr_text_on.

    This avoids the timeout issues with the ontobio map2slim by:
    1. Using gu_run_solr_text_on with 60-second timeout
    2. Requesting only necessary fields
    3. Processing the slimming logic locally
    """
    # Convert single slim term to list if needed
    if isinstance(slim_terms, str):
        slim_terms = [slim_terms]

    # Clean up slim terms - handle comma-separated strings
    cleaned_slim_terms = []
    for term in slim_terms:
        if ',' in term:
            cleaned_slim_terms.extend([t.strip() for t in term.split(',')])
        else:
            cleaned_slim_terms.append(term.strip())
    slim_terms = cleaned_slim_terms

    results = []

    for subject_id in subjects:
        # Build the query
        q = "*:*"
        qf = ""
        fq = f'&fq=bioentity:"{subject_id}"'

        # Only request necessary fields for slimming
        fields = ("id,bioentity,bioentity_label,annotation_class,annotation_class_label,"
                  "regulates_closure,aspect,evidence_type,evidence_type_label,"
                  "taxon,taxon_label,assigned_by,reference")

        # Apply evidence filters
        if exclude_automatic_assertions:
            fq += '&fq=!evidence_type:("IEA")'

        # Apply relationship type filter if not default
        if relationship_type == "involved_in":
            # For involved_in, we only want direct annotations
            fq += '&fq=qualifier:"involved_in"'
        # For acts_upstream_of_or_within, we want all relationships

        # Set rows to fetch all annotations for this subject
        fq += "&rows=100000"

        # Make the request with 60-second timeout
        try:
            # gu_run_solr_text_on expects enum objects, not strings
            annotations = gu_run_solr_text_on(
                ESOLR.GOLR,
                ESOLRDoc.ANNOTATION,
                q, qf, fields, fq,
                highlight=False
            )
            logger.info(f"Found {len(annotations)} annotations for {subject_id}")
        except Exception as e:
            logger.error(f"Error fetching annotations for {subject_id}: {e}")
            continue

        # Process annotations into slim groups
        slim_map = {}
        subject_info = None

        for annot in annotations:
            # Get subject info from first annotation
            if subject_info is None:
                subject_info = {
                    "id": annot.get("bioentity", ""),
                    "label": annot.get("bioentity_label", ""),
                    "taxon": {
                        "id": annot.get("taxon", ""),
                        "label": annot.get("taxon_label", "")
                    }
                }

            # Get the regulates_closure (object_closure)
            regulates_closure = annot.get("regulates_closure", [])
            if isinstance(regulates_closure, str):
                regulates_closure = [regulates_closure]

            # Find which slim terms this annotation maps to
            for slim_term in slim_terms:
                if slim_term in regulates_closure:
                    if slim_term not in slim_map:
                        slim_map[slim_term] = []

                    # Create association object matching map2slim format
                    assoc = {
                        "id": annot.get("id", ""),
                        "subject": subject_info,
                        "object": {
                            "id": annot.get("annotation_class", ""),
                            "label": annot.get("annotation_class_label", "")
                        },
                        "relation": {
                            "id": relationship_type,
                            "label": relationship_type.replace("_", " ")
                        },
                        "evidence": [
                            {
                                "id": annot.get("evidence_type", ""),
                                "label": annot.get("evidence_type_label", "")
                            }
                        ],
                        "provided_by": [annot.get("assigned_by", "")] if annot.get("assigned_by") else [],
                        "publications": [annot.get("reference", "")] if annot.get("reference") else []
                    }
                    slim_map[slim_term].append(assoc)

        # Format results to match map2slim output
        for slim_term, assocs in slim_map.items():
            result = {
                "subject": subject_id,
                "slim": slim_term,
                "assocs": assocs
            }
            results.append(result)

    return results
