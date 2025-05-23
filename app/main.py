"""main application entry point."""

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.exceptions.global_exceptions import DataNotFoundException
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import (
    bioentity,
    labeler,
    models,
    ontology,
    pathway_widget,
    prefixes,
    ribbon,
    search,
    slimmer,
    users_and_groups,
)

logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="GO API",
    description="The Gene Ontology API.\n\n __Source:__ 'https://github.com/geneontology/go-fastapi'",
    version="1.0.0",
    contact={
        "name": "Gene Ontology Consortium",
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
app.include_router(users_and_groups.router)

# Logging
app.add_middleware(LoggingMiddleware)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for ValueErrors
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Global exception handler for ValueErrors.

    :param request:
    :param exc:
    :return:
    """
    logger.error(f"Value error occurred: {exc}")
    return JSONResponse(status_code=400, content={"message": f"Value error occurred: {exc}"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all other exceptions."""
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )


@app.exception_handler(DataNotFoundException)
async def data_not_found_exception_handler(request: Request, exc: DataNotFoundException):
    """
    Global exception handler for DataNotFoundException.

    :param request:
    :param exc:
    :return:
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, log_level="info", reload=True)
