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
    Decorator to retry tests that fail due to Golr 522 errors.

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
                except Exception:
                    raise
            if last_exception:
                pytest.skip(f"Golr unavailable after {max_retries} retries: {last_exception}")
        return wrapper
    return decorator