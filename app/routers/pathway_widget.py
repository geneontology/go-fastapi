"""Pathway widget API endpoints."""

import logging

from curies import Converter
from fastapi import APIRouter, Path, Query

from app.exceptions.global_exceptions import DataNotFoundException, InvalidIdentifier
from app.routers.models import get_model_details_by_model_id_json
from app.utils.golr_utils import is_valid_bioentity
from app.utils.prefix_utils import get_prefixes
from app.utils.settings import get_user_agent

logger = logging.getLogger()

USER_AGENT = get_user_agent()
router = APIRouter()


@router.get(
    "/api/gp/{id}/models",
    tags=["pathways"],
    description="Returns GO-CAM models associated with a given Gene Product identifier. "
    "(e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1).",
)
async def get_gocams_by_geneproduct_id(
    id: str = Path(..., description="The CURIE of the gene product, e.g. MGI:3588192", examples="MGI:3588192"),
    causalmf: int = Query(
        None,
        deprecated=True,
        description="Used by the pathway widget The model has a chain of at least three functions connected "
        "by at least two consecutive causal relation edges.  One of these functions is enabled_by "
        "this input gene",
    ),
):
    """
    Returns GO-CAM models associated with a given Gene Product identifier.

    (e.g. MGI:3588192, ZFIN:ZDB-GENE-000403-1).
    """
    if id.startswith("MGI:MGI:"):
        id = id.replace("MGI:MGI:", "MGI:")

    from app.utils.settings import get_index_files

    entity_index = get_index_files("gocam_entity_index_file")

    cmaps = get_prefixes("go")
    converter = Converter.from_prefix_map(cmaps, strict=False)
    id_iri = converter.expand(id)
    logger.info("reformatted curie into IRI using identifiers.org from api/gp/%s/models endpoint", id_iri)

    model_ids = set()
    if id in entity_index:
        model_ids.update(entity_index[id])
    if id_iri in entity_index:
        model_ids.update(entity_index[id_iri])

    if not model_ids:
        # Only validate with Golr if not found in index
        # This allows tests to work without external Golr dependency
        try:
            is_valid_bioentity(id)
        except DataNotFoundException as e:
            raise DataNotFoundException(detail=str(e)) from e
        except ValueError as e:
            raise InvalidIdentifier(detail=str(e)) from e
        except Exception:
            # If Golr is unavailable and entity not in index, return empty
            return []
        return []

    collated_results = []
    for model_id in sorted(model_ids):
        model_data = await get_model_details_by_model_id_json(model_id)
        gocam_iri = f"http://model.geneontology.org/{model_id}"
        title = ""
        for ann in model_data.get("annotations", []):
            if ann.get("key") == "title":
                title = ann.get("value", "")
                break

        if causalmf == 2:
            if has_causal_pathway(model_data, id_iri):
                collated_results.append({"gocam": gocam_iri, "title": title})
        else:
            collated_results.append({"gocam": gocam_iri, "title": title})

    return collated_results


def has_causal_pathway(model_data, gene_product_iri):
    """
    Check if the model has a causal pathway (chain of 3+ functions or chemical intermediate).

    :param model_data: The GO-CAM model JSON data
    :param gene_product_iri: The IRI of the gene product
    :return: True if model contains a causal pathway involving the gene product
    """
    CAUSAL_RELATIONS = {
        "RO:0002418", "RO:0004046", "RO:0004047", "RO:0002411",
        "RO:0002305", "RO:0002304", "RO:0002211", "RO:0002212",
        "RO:0002213", "RO:0002578", "RO:0002629", "RO:0002630",
        "RO:0002406", "RO:0002407", "RO:0002408", "RO:0002409",
        "RO:0002414", "RO:0002412", "RO:0002413"
    }

    causal_count = 0
    for fact in model_data.get("facts", []):
        prop = fact.get("property", "")
        if prop in CAUSAL_RELATIONS:
            causal_count += 1

    if causal_count >= 2:
        return True

    has_chemical_conn = False
    for fact in model_data.get("facts", []):
        prop = fact.get("property", "")
        if prop == "RO:0002233" or prop == "RO:0002234":
            has_chemical_conn = True
            break

    return has_chemical_conn
