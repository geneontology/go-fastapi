"""Retry utilities for external API calls."""

import time
from functools import wraps
from typing import Any, Callable


def retry_on_golr_error(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to retry GOLr/Solr calls on server errors.

    This unified decorator handles retry logic for both direct Solr queries
    and ontobio library calls.

    :param max_retries: Maximum number of retry attempts
    :param delay: Delay in seconds between retries
    :return: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.utils.settings import logger

            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    error_type = type(e).__name__

                    # Check for server errors in the error message or error type
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
            else:
                # This should never happen, but ensures no implicit None return
                raise RuntimeError(f"All {max_retries} attempts failed without capturing an exception")

        return wrapper
    return decorator