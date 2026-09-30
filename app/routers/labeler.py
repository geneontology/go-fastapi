"""Provides a route for fetching labels for CURIEs/IDs."""

import logging
from typing import List

from fastapi import APIRouter, Query

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.golr_utils import validate_solr_filter_values
from app.utils.ontology_utils import batch_fetch_labels
from app.utils.settings import get_user_agent

USER_AGENT = get_user_agent()
router = APIRouter()

logger = logging.getLogger()


@router.get(
    "/api/ontol/labeler", tags=["ontol/labeler"], description="Fetches a map from IDs to labels e.g. GO:0003677."
)
async def expand_curie(
    id: List[str] = Query(..., description="IDs to fetch labels for.", examples=["GO:0003677", "GO:0008150"])
):
    """Fetches a map from IDs to labels e.g. GO:0003677."""
    # Refused here for a clear 400; the per-id lookup below turns any error into "no label".
    validate_solr_filter_values(id, "id")
    logger.info("fetching labels for IDs")
    labels = batch_fetch_labels(id)
    if not labels:
        raise DataNotFoundException(detail=f"Item with ID {id} not found")
    return labels
