from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def setup_static_files(app: FastAPI) -> None:
    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMPLATES_DIR = BASE_DIR / "templates"

    app.mount("/", StaticFiles(directory=TEMPLATES_DIR, html=True), name="templates")
