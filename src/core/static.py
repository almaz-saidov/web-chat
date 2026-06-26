from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def setup_static_files(app: FastAPI) -> None:
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = BASE_DIR / "static"

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
