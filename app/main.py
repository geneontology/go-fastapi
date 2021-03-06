import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from app.routers import bioentity
from app.routers import labeler
from app.routers import ontology
from app.routers import ribbon
from app.routers import prefixes
from app.routers import search
from app.routers import slimmer

log = logging.getLogger(__name__)

app = FastAPI(title="GO API",
              description="Gene Ontology API based on the BioLink Model, an integration layer for linked biological "
                          "objects.\n\n __Source:__ 'https://github.com/geneontology/biolink-api'",
              version="1.0.0",
              terms_of_service="http://example.com/terms/",
              contact={
                  "name": "Gene Ontology Consortium Software Development Team",
                  "url": "https://help.geneontology.org",
                  "email": "help@geneontology.org",
              },
              license_info={
                  "name": "BSD3"
              }, )
app.include_router(bioentity.router)
app.include_router(slimmer.router)
app.include_router(prefixes.router)
app.include_router(labeler.router)
app.include_router(ontology.router)
app.include_router(ribbon.router)
app.include_router(search.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.mount("/static", StaticFiles(directory="static"), name="static")
#
#
# @app.get("/")
# async def read_index():
#     return FileResponse('static/index.html')

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8080)
