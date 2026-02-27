from fastapi import WebSocket, WebSocketDisconnect

from core.connection_manager import manager


class WebSocketService:
    async def handle_websocket(self, websocket: WebSocket, username: str) -> None:
        await self._connect(websocket=websocket, username=username)

        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(message=f"{username}: {data}")

        except WebSocketDisconnect:
            await self._disconnect(websocket=websocket)

    async def _connect(self, websocket: WebSocket, username: str) -> None:
        await manager.connect(websocket=websocket, username=username)

    async def _disconnect(self, websocket: WebSocket) -> None:
        manager.disconnect(websocket=websocket)


def get_websocket_service() -> WebSocketService:
    return WebSocketService()
