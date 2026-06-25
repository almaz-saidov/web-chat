from typing import cast
from unittest.mock import AsyncMock, Mock

from fastapi import WebSocket

from core.connection_manager import ConnectionManager


def make_websocket_mock() -> Mock:
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock(return_value=None)
    websocket.send_text = AsyncMock(return_value=None)
    return websocket


async def test_connect_accepts_websocket_and_stores_username() -> None:
    manager = ConnectionManager()
    websocket = make_websocket_mock()

    await manager.connect(websocket=cast(WebSocket, websocket), username="almaz")

    websocket.accept.assert_awaited_once_with()
    assert manager.active_connections[cast(WebSocket, websocket)] == "almaz"


def test_disconnect_removes_active_connection() -> None:
    manager = ConnectionManager()
    websocket = make_websocket_mock()
    manager.active_connections[cast(WebSocket, websocket)] = "almaz"

    manager.disconnect(websocket=cast(WebSocket, websocket))

    assert cast(WebSocket, websocket) not in manager.active_connections


async def test_broadcast_sends_message_to_all_active_connections() -> None:
    manager = ConnectionManager()
    first_websocket = make_websocket_mock()
    second_websocket = make_websocket_mock()
    manager.active_connections[cast(WebSocket, first_websocket)] = "almaz"
    manager.active_connections[cast(WebSocket, second_websocket)] = "saidov"

    await manager.broadcast(message="hello")

    first_websocket.send_text.assert_awaited_once_with("hello")
    second_websocket.send_text.assert_awaited_once_with("hello")
