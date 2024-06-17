"""Middleware to log requests."""

import logging

from fastapi import Request
from fastapi.logger import logger as fastapi_logger
from starlette.middleware.base import BaseHTTPMiddleware

fastapi_logger.setLevel(logging.INFO)
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LoggingMiddleware(BaseHTTPMiddleware):

    """Middleware to log requests."""

    async def dispatch(self, request: Request, call_next):
        """
        Log requests.

        :param request: The request.
        :param call_next: The next call.
        :param logger: The logger.
        :return: The response.
        """
        # Log request method and URL
        logger.info(f"Request URL: {request.url} | Method: {request.method}")

        # Log request headers
        # logger.info(f"Headers: {dict(request.headers)}")

        # If you need the request body, handle with care:
        # body = await request.body()
        # logger.info(f"Body: {body.decode()}")
        #
        # Since the body is read and can't be read again,
        # you need to make it available for the actual route again
        # request._body = body

        response = await call_next(request)
        return response
