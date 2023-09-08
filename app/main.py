"""main application entry point."""
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import (
    bioentity,
    labeler,
    models,
    ontology,
    pathway_widget,
    prefixes,
    publications,
    ribbon,
    search,
    slimmer,
    users_and_groups,
)

log = logging.getLogger(__name__)

app = FastAPI(
    title="GO API",
    description="The Gene Ontology API.\n\n __Source:__ 'https://github.com/geneontology/go-fastapi'",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Gene Ontology Consortium Software Development Team",
        "url": "https://help.geneontology.org",
        "email": "help@geneontology.org",
    },
    license_info={"name": "BSD3"},
)
app.include_router(ontology.router)
app.include_router(bioentity.router)
app.include_router(ribbon.router)
app.include_router(pathway_widget.router)
app.include_router(slimmer.router)
app.include_router(models.router)
app.include_router(prefixes.router)
app.include_router(labeler.router)
app.include_router(search.router)
app.include_router(publications.router)
app.include_router(users_and_groups.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoggingMiddleware(BaseHTTPMiddleware):

    """Middleware to log requests."""

    async def dispatch(self, request: Request, call_next):
        """
        Log requests.

        :param request: The request.
        :param call_next: The next call.
        :return: The response.
        """
        # Log request method and URL
        print(f"Request URL: {request.url} | Method: {request.method}")

        # Log request headers
        print(f"Headers: {dict(request.headers)}")

        # # If you need the request body, handle with care:
        # body = await request.body()
        # print(f"Body: {body.decode()}")
        #
        # # Since the body is read and can't be read again,
        # # you need to make it available for the actual route again
        # request._body = body

        response = await call_next(request)
        return response


app.add_middleware(LoggingMiddleware)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080)
