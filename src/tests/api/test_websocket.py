import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, WebSocket, status
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from api.dependencies import get_current_user_from_ws
from core.connection_manager import manager
from schemas.user import UserSchema


def make_user_schema(username: str = "almaz") -> UserSchema:
    return UserSchema(
        id=uuid.uuid4(),
        username=username,
        password_hash="password-hash",
        created_at=datetime.now(timezone.utc),
    )


def test_websocket_returns_1008_without_token(test_app: FastAPI) -> None:
    with TestClient(test_app) as client:
        with pytest.raises(WebSocketDisconnect) as exception_info:
            with client.websocket_connect("/api/ws"):
                pass

    assert exception_info.value.code == status.WS_1008_POLICY_VIOLATION, (
        "WebSocket endpoint must reject connection without token"
    )


def test_websocket_returns_1008_for_invalid_token(test_app: FastAPI, jwt_keys: None) -> None:
    with TestClient(test_app) as client:
        with pytest.raises(WebSocketDisconnect) as exception_info:
            with client.websocket_connect("/api/ws?token=invalid-token"):
                pass

    assert exception_info.value.code == status.WS_1008_POLICY_VIOLATION, (
        "WebSocket endpoint must reject connection with invalid token"
    )


def test_websocket_broadcasts_message_for_authorized_user(test_app: FastAPI) -> None:
    async def override_get_current_user_from_ws(websocket: WebSocket) -> UserSchema:
        token = websocket.query_params.get("token")

        assert token == "access-token", "WebSocket auth override must receive access token from query params"
        return make_user_schema(username="almaz")

    original_overrides = dict(test_app.dependency_overrides)
    test_app.dependency_overrides[get_current_user_from_ws] = override_get_current_user_from_ws
    manager.active_connections.clear()

    try:
        with TestClient(test_app) as client:
            with client.websocket_connect("/api/ws?token=access-token") as websocket:
                websocket.send_text("hello")
                message = websocket.receive_text()

        assert message == "almaz: hello", "WebSocket endpoint must broadcast message with username prefix"
        assert not manager.active_connections, "WebSocket endpoint must disconnect user after client closes"
    finally:
        manager.active_connections.clear()
        test_app.dependency_overrides.clear()
        test_app.dependency_overrides.update(original_overrides)
