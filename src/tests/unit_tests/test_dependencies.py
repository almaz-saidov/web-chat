import uuid
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket
from fastapi.security import HTTPAuthorizationCredentials
from starlette.datastructures import QueryParams

from api.dependencies import get_current_user, get_current_user_from_ws
from core.exceptions import TokenIsRequiredWebSocketException
from schemas.user import UserSchema
from services.auth_service import AuthService


def make_user_schema() -> UserSchema:
    return UserSchema(
        id=uuid.uuid4(),
        username="almaz",
        password_hash="password-hash",
        created_at=datetime.now(timezone.utc),
    )


def make_auth_service_mock(user: UserSchema) -> Mock:
    auth_service = Mock(spec=AuthService)
    auth_service.authorize_user = AsyncMock(return_value=user)
    auth_service.authorize_websocket_user = AsyncMock(return_value=user)
    return auth_service


def make_websocket_mock(query_params: dict[str, str] | None = None) -> Mock:
    websocket = Mock(spec=WebSocket)
    websocket.query_params = QueryParams(query_params or {})
    return websocket


async def test_get_current_user_authorizes_credentials_token() -> None:
    user = make_user_schema()
    auth_service = make_auth_service_mock(user=user)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="access-token"
    )

    result = await get_current_user(
        credentials=credentials,
        auth_service=cast(AuthService, auth_service),
    )

    assert result == user, (
        "Current user dependency must return the user authorized by AuthService"
    )
    auth_service.authorize_user.assert_awaited_once_with("access-token")


async def test_get_current_user_from_ws_authorizes_query_token() -> None:
    user = make_user_schema()
    auth_service = make_auth_service_mock(user=user)
    websocket = make_websocket_mock(query_params={"token": "access-token"})

    result = await get_current_user_from_ws(
        websocket=cast(WebSocket, websocket),
        auth_service=cast(AuthService, auth_service),
    )

    assert result == user, (
        "WebSocket user dependency must return the user authorized by AuthService"
    )
    auth_service.authorize_websocket_user.assert_awaited_once_with("access-token")


async def test_get_current_user_from_ws_raises_error_when_token_is_missing() -> None:
    user = make_user_schema()
    auth_service = make_auth_service_mock(user=user)

    with pytest.raises(TokenIsRequiredWebSocketException):
        await get_current_user_from_ws(
            websocket=cast(WebSocket, make_websocket_mock()),
            auth_service=cast(AuthService, auth_service),
        )

    auth_service.authorize_websocket_user.assert_not_awaited()
