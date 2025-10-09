"""The users and groups endpoints."""
import logging

from fastapi import APIRouter, Path

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.settings import get_index_files, get_user_agent

logger = logging.getLogger()
USER_AGENT = get_user_agent()
router = APIRouter()

@router.get("/api/users/{orcid}/gp", tags=["models"], description="Get GPs by orcid", deprecated=True)
async def get_gp_models_by_orcid(
    orcid: str = Path(
        ...,
        description="The ORCID of the user (e.g. 0000-0002-7285-027X)",
        example="0000-0002-7285-027X",
    )
):
    """Returns GO-CAM model identifiers for a particular contributor orcid."""
    contributor_index = get_index_files("gocam_contributor_index_file")

    orcid_url = f"https://orcid.org/{orcid}"

    if orcid_url not in contributor_index:
        raise DataNotFoundException(detail=f"Item with ID {orcid} not found")

    return contributor_index[orcid_url]
