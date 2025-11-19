"""Test utilities for handling flaky external dependencies."""

import functools
import time

import pytest
import requests


def check_golr_availability():
    """
    Check if Golr is available by making a simple request.

    Returns:
        bool: True if Golr is available, False otherwise
    """
    try:
        response = requests.get(
            "https://golr.geneontology.org/solr/select?q=*:*&rows=0&wt=json",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def retry_on_golr_error(max_retries=3, delay=2):
    """
    Decorator to retry tests that fail due to Golr errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries

    Returns:
        Decorated test function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if "522" in str(e):
                        last_exception = e
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                            continue
                    raise
                except Exception as e:
                    # Handle pysolr.SolrError and other connection errors
                    error_str = str(e)
                    error_type = type(e).__name__
                    error_module = type(e).__module__
                    print(f"Caught exception on attempt {attempt + 1}: {error_module}.{error_type}")
                    print(f"Error message: {error_str}")
                    if hasattr(e, 'args') and e.args:
                        print(f"Error args: {e.args}")
                    
                    # Be very broad in what we consider retryable GOLr errors
                    retryable_errors = ["connection", "timeout", "solrerror", "522", "502", "server", "http", 
                                      "bad gateway", "service unavailable", "gateway timeout", "read timed out"]
                    retryable_types = ["solrerror", "connectionerror", "timeout", "httperror", "requestexception"]
                    
                    if any(err in error_str.lower() for err in retryable_errors) or \
                       any(err in error_type.lower() for err in retryable_types):
                        last_exception = e
                        if attempt < max_retries - 1:
                            print(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                            continue
                        else:
                            print(f"Max retries ({max_retries}) reached")
                    else:
                        print(f"Error not considered retryable, re-raising")
                    raise
            if last_exception:
                raise last_exception
        return wrapper
    return decorator