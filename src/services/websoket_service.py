from fastapi import WebSocket, WebSocketDisconnect

from core.connection_manager import manager


class WebSocketService:
    async def handle_websocket(self, websocket: WebSocket, username: str) -> None:
        await self._connect(websocket, username)

        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(f"{username}: {data}")

        except WebSocketDisconnect:
            await self._disconnect(websocket)

    async def _connect(self, websocket: WebSocket, username: str) -> None:
        await manager.connect(websocket, username)
        await manager.broadcast(f"{username} joined the chat.")

    async def _disconnect(self, websocket: WebSocket) -> None:
        disconnected_user = manager.disconnect(websocket)
        if disconnected_user:
            await manager.broadcast(f"{disconnected_user} left the chat.")


def get_websocket_service() -> WebSocketService:
    return WebSocketService()
