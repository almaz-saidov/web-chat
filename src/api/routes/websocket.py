from fastapi import APIRouter, WebSocket

from services.websoket_service import get_websocket_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str = "Guest"):
    websocket_service = get_websocket_service()
    await websocket_service.handle_websocket(websocket, username)
