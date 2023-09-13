"""main application entry point."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.logging_middleware import LoggingMiddleware
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
app.include_router(publications.router)
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, log_level="info", reload=True)
