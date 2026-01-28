from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from websoket.connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str = "Guest"):
    await manager.connect(websocket, username)

    await manager.broadcast(f"{username} joined the chat.")

    try:
        while True:
            data = await websocket.receive_text()

            await manager.broadcast(f"{username}: {data}")

    except WebSocketDisconnect:
        disconnected_user = manager.disconnect(websocket)
        if disconnected_user:
            await manager.broadcast(f"{disconnected_user} left the chat.")
