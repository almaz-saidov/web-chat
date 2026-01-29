from typing import Optional

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, str] = dict()

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self.active_connections[websocket] = username

    def disconnect(self, websocket: WebSocket) -> Optional[str]:
        if websocket in self.active_connections:
            username = self.active_connections[websocket]
            del self.active_connections[websocket]
            return username

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()
