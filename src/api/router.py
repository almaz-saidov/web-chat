from fastapi import APIRouter

from api.healthcheck import router as healthcheck_router
from api.routes.auth import router as auth_router
from api.routes.messages import router as messages_router
from api.routes.websocket import router as ws_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(healthcheck_router)
router.include_router(messages_router)
router.include_router(ws_router)
