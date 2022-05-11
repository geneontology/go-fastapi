from fastapi import FastAPI
import uvicorn
import logging
from .routers import slimmer
log = logging.getLogger(__name__)

app = FastAPI()
app.include_router(slimmer.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=80)
