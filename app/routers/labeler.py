import logging
from fastapi import APIRouter, Query
from ontobio.util.user_agent import get_user_agent
from ontobio.sparql.sparql_ontol_utils import batch_fetch_labels
from typing import List

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent(name="go-fastapi", version="0.1.0")
router = APIRouter()


@router.get("/api/ontol/labeler", tags=["ontol/labeler"])
async def expand_curie(id: List[str] = Query(...)):
        """
        Fetches a map from CURIEs/IDs to labels
        """

        return batch_fetch_labels(id)


    
    

