from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from .routers import slimmer
log = logging.getLogger(__name__)

app = FastAPI()
app.include_router(slimmer.router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=80)
