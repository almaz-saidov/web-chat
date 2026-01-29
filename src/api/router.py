from fastapi import APIRouter

from api.routes.websocket import router as ws_router

router = APIRouter(prefix="/api")

router.include_router(ws_router)
