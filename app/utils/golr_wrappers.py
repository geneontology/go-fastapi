"""Wrappers for external library functions that need rate limiting."""

from typing import Any, Dict, List, Optional

from ontobio.golr.golr_associations import map2slim as _map2slim
from ontobio.golr.golr_associations import search_associations as _search_associations

from app.utils.rate_limiter import rate_limit_golr, retry_on_golr_error


@retry_on_golr_error(max_retries=3, delay=2)
@rate_limit_golr
def search_associations(
    subject_category: Optional[str] = None,
    object_category: Optional[str] = None,
    subject: Optional[str] = None,
    object: Optional[str] = None,
    subject_taxon: Optional[List[str]] = None,
    relation: Optional[str] = None,
    evidence: Optional[str] = None,
    slim: Optional[List[str]] = None,
    use_compact_associations: bool = False,
    fq: Optional[Dict[str, Any]] = None,
    user_agent: Optional[str] = None,
    url: Optional[str] = None,
    start: Optional[int] = None,
    rows: Optional[int] = None,
    facet_fields: Optional[List[str]] = None,
    facet_limit: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rate-limited wrapper for ontobio's search_associations function.

    This wrapper adds rate limiting to prevent hitting GOLr API limits.
    All parameters are passed through to the original function.
    """
    # Build kwargs dynamically to exclude None values
    call_kwargs = {}

    if subject_category is not None:
        call_kwargs['subject_category'] = subject_category
    if object_category is not None:
        call_kwargs['object_category'] = object_category
    if subject is not None:
        call_kwargs['subject'] = subject
    if object is not None:
        call_kwargs['object'] = object
    if subject_taxon is not None:
        call_kwargs['subject_taxon'] = subject_taxon
    if relation is not None:
        call_kwargs['relation'] = relation
    if evidence is not None:
        call_kwargs['evidence'] = evidence
    if slim is not None:
        call_kwargs['slim'] = slim
    call_kwargs['use_compact_associations'] = use_compact_associations
    if fq is not None:
        call_kwargs['fq'] = fq
    if user_agent is not None:
        call_kwargs['user_agent'] = user_agent
    if url is not None:
        call_kwargs['url'] = url
    if start is not None:
        call_kwargs['start'] = start
    if rows is not None:
        call_kwargs['rows'] = rows
    if facet_fields is not None:
        call_kwargs['facet_fields'] = facet_fields
    if facet_limit is not None:
        call_kwargs['facet_limit'] = facet_limit

    # Add any additional kwargs
    call_kwargs.update(kwargs)

    return _search_associations(**call_kwargs)


@retry_on_golr_error(max_retries=3, delay=2)
@rate_limit_golr
def map2slim(
    subjects: List[str],
    slim: List[str],
    object_category: str = "function",
    user_agent: Optional[str] = None,
    url: Optional[str] = None,
    relationship_type: str = "involved_in",
    exclude_automatic_assertions: bool = False,
    rows: int = -1,
    start: int = 0,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Rate-limited wrapper for ontobio's map2slim function.

    This wrapper adds rate limiting to prevent hitting GOLr API limits.
    All parameters are passed through to the original function.
    """
    return _map2slim(
        subjects=subjects,
        slim=slim,
        object_category=object_category,
        user_agent=user_agent,
        url=url,
        relationship_type=relationship_type,
        exclude_automatic_assertions=exclude_automatic_assertions,
        rows=rows,
        start=start,
        **kwargs
    )
