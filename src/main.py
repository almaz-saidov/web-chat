import uvicorn
from fastapi import FastAPI

from core.config import settings
from core.static import setup_static_files
from websoket.router import router as ws_router

app = FastAPI()

app.include_router(ws_router)

setup_static_files(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT)
