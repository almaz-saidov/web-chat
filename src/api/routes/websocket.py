from fastapi import APIRouter, Depends, WebSocket

from api.dependesies import get_current_user_from_ws
from database.models import User
from services.websoket_service import WebSocketService, get_websocket_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    websocket_service: WebSocketService = Depends(get_websocket_service),
    user: User = Depends(get_current_user_from_ws),
):
    await websocket_service.handle_websocket(websocket, user.username)
