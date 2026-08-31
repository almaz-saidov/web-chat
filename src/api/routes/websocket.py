from fastapi import APIRouter, Depends, WebSocket

from api.dependencies import get_current_user_from_ws
from schemas.user import UserSchema
from services.websocket import WebSocketService

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    websocket_service: WebSocketService = Depends(),
    user: UserSchema = Depends(get_current_user_from_ws),
) -> None:
    await websocket_service.handle_websocket(
        websocket=websocket, username=user.username
    )
