import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (bioentity, labeler, ontology, prefixes, ribbon,
                         search, slimmer, models, users_and_groups)

log = logging.getLogger(__name__)

app = FastAPI(
    title="GO API",
    description="Gene Ontology API based on the BioLink Model, an integration layer for linked biological "
    "objects.\n\n __Source:__ 'https://github.com/geneontology/go-fastapi'",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Gene Ontology Consortium Software Development Team",
        "url": "https://help.geneontology.org",
        "email": "help@geneontology.org",
    },
    license_info={"name": "BSD3"},
)
app.include_router(bioentity.router)
app.include_router(slimmer.router)
app.include_router(prefixes.router)
app.include_router(labeler.router)
app.include_router(ontology.router)
app.include_router(ribbon.router)
app.include_router(search.router)
app.include_router(models.router)
app.include_router(users_and_groups.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
