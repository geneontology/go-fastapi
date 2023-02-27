import logging
from typing import List

from fastapi import APIRouter, Query
from app.utils.ontology.ontology_utils import batch_fetch_labels
from ontobio.util.user_agent import get_user_agent

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.1")
router = APIRouter()


@router.get("/api/ontol/labeler", tags=["ontol/labeler"])
async def expand_curie(id: List[str] = Query(...)):
    """
    Fetches a map from CURIEs/IDs to labels
    """

    return batch_fetch_labels(id)
