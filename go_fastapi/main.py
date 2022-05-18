from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import routers.bioentity, routers.slimmer, routers.prefixes, routers.labeler, routers.ontology, routers.search
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(routers.bioentity.router)
app.include_router(routers.slimmer.router)
app.include_router(routers.prefixes.router)
app.include_router(routers.labeler.router)
app.include_router(routers.ontology.router)
app.include_router(routers.search.router)

app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_methods=["*"],
                   allow_headers=["*"])
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000)
