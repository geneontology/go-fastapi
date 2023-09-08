"""Provides a route for fetching labels for CURIEs/IDs."""
import logging
from typing import List

from fastapi import APIRouter, Query

from app.utils.ontology_utils import batch_fetch_labels
from app.utils.settings import get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()


@router.get("/api/ontol/labeler", tags=["ontol/labeler"])
async def expand_curie(id: List[str] = Query(...,
                                             description="IDs to fetch labels for.",
                                             example=["GO:0003677", "MGI:3588192"])):
    """Fetches a map from IDs to labels e.g. GO:0003677."""
    for i in id:
        if "MGI:MGI" in i:
            id.remove(i)
            id.append(i.replace("MGI:MGI", "MGI:"))

    return batch_fetch_labels(id)
