"""Rate limiting utilities for external API calls."""

import time
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict


class RateLimiter:

    """Simple rate limiter using a token bucket algorithm."""

    def __init__(self, calls_per_second: float = 2.0):
        """
        Initialize the rate limiter.

        :param calls_per_second: Maximum number of calls allowed per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
        self.lock = Lock()

    def wait_if_needed(self) -> None:
        """Wait if necessary to maintain the rate limit."""
        with self.lock:
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time

            if time_since_last_call < self.min_interval:
                sleep_time = self.min_interval - time_since_last_call
                time.sleep(sleep_time)
                self.last_call_time = time.time()
            else:
                self.last_call_time = current_time


# Global rate limiter instances for different services
_rate_limiters: Dict[str, RateLimiter] = {}
_rate_limiter_lock = Lock()


def get_rate_limiter(service: str = "default", calls_per_second: float = 2.0) -> RateLimiter:
    """
    Get or create a rate limiter for a specific service.

    :param service: Name of the service (e.g., "golr", "mygene")
    :param calls_per_second: Maximum calls per second for this service
    :return: RateLimiter instance
    """
    with _rate_limiter_lock:
        if service not in _rate_limiters:
            _rate_limiters[service] = RateLimiter(calls_per_second)
        return _rate_limiters[service]


def rate_limit(service: str = "default", calls_per_second: float = 2.0) -> Callable:
    """
    Decorator to rate limit function calls.

    :param service: Name of the service being rate limited
    :param calls_per_second: Maximum calls per second
    :return: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            rate_limiter = get_rate_limiter(service, calls_per_second)
            rate_limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Specific rate limiter for GOLr API calls
def rate_limit_golr(func: Callable) -> Callable:
    """
    Decorator specifically for GOLr API calls with conservative rate limiting.

    Uses 0.33 calls per second (1 call every 3 seconds) to avoid hitting rate limits.
    """
    return rate_limit(service="golr", calls_per_second=0.33)(func)


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

        return wrapper
    return decorator

