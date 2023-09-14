"""Provides a route for fetching labels for CURIEs/IDs."""
import logging
from typing import List

from fastapi import APIRouter, Query

from app.utils.ontology_utils import batch_fetch_labels
from app.utils.settings import get_user_agent

USER_AGENT = get_user_agent()
router = APIRouter()

logger = logging.getLogger()


@router.get("/api/ontol/labeler",
            tags=["ontol/labeler"],
            description="Fetches a map from IDs to labels e.g. GO:0003677.")
async def expand_curie(
    id: List[str] = Query(...,
                          description="IDs to fetch labels for.", 
                          example=["GO:0003677", "GO:0008150"])
):
    """Fetches a map from IDs to labels e.g. GO:0003677."""
    logger.info("fetching labels for IDs")
    return batch_fetch_labels(id)
