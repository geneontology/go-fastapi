"""Wrappers for external library functions that need rate limiting."""

import time
from typing import Any, Dict, List, Optional

from ontobio.golr.golr_associations import map2slim as _map2slim
from ontobio.golr.golr_associations import search_associations as _search_associations

from app.utils.rate_limiter import rate_limit_golr
from app.utils.settings import logger


def retry_on_golr_server_error(max_retries=3, delay=2):
    """
    Decorator to retry ontobio GOLr calls on server errors.

    :param max_retries: Maximum number of retry attempts
    :param delay: Delay in seconds between retries
    :return: Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    error_type = type(e).__name__

                    # Check for server errors in the error message
                    server_errors = ['502', '522', '503', '504', '400', 'bad gateway', 'server error',
                                   'connection', 'timeout', 'solrerror', 'read timeout', 'readtimeout',
                                   'timed out']

                    if any(err in error_str.lower() for err in server_errors) or \
                       'solrerror' in error_type.lower():
                        last_exception = e
                        logger.info(
                            f"GOLr server error on attempt {attempt + 1}/{max_retries}: "
                            f"{error_type}: {error_str}"
                        )
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                            continue
                    raise
            # If we get here, all retries failed
            if last_exception:
                logger.error(f"All {max_retries} GOLr attempts failed, raising last exception")
                raise last_exception
        return wrapper
    return decorator


@retry_on_golr_server_error(max_retries=3, delay=2)
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
    if use_compact_associations is not None:
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


@retry_on_golr_server_error(max_retries=3, delay=2)
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
