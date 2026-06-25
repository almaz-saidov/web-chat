import uuid
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import bcrypt
import pytest
from fastapi import Request, Response
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from core.exceptions import (
    AccessTokenExpiredHTTPException,
    InvalidTokenHTTPException,
    RefreshTokenExpiredHTTPException,
    TokenIsInvalidOrExpiredWebSocketException,
    UserAlreadyExistsHTTPException,
    WrongUsernameOrPasswordHTTPException,
)
from schemas.jwt import JWTPayloadSchema
from schemas.refresh_token import RefreshTokenCreateSchema, RefreshTokenSchema
from schemas.user import UserCreateDatabaseSchema, UserCreateSchema, UserLoginSchema, UserSchema
from services.auth_service import AuthService
from services.cookies_service import CookiesService
from services.jwt_service import JWTService
from services.refresh_token_service import RefreshTokenService
from services.user_service import UserService


def make_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def make_user_schema(
    user_id: uuid.UUID | None = None,
    username: str = "almaz",
    password_hash: str | None = None,
) -> UserSchema:
    return UserSchema(
        id=user_id or uuid.uuid4(),
        username=username,
        password_hash=password_hash or make_password_hash("secret123"),
        created_at=datetime.now(timezone.utc),
    )


def make_refresh_token_schema(
    user_id: uuid.UUID | None = None,
    refresh_token: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> RefreshTokenSchema:
    return RefreshTokenSchema(
        id=1,
        user_id=user_id or uuid.uuid4(),
        refresh_token=refresh_token or uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=1),
    )


def make_request() -> Request:
    return Request({"type": "http", "headers": []})


def make_jwt_service_mock(
    payload: JWTPayloadSchema | None = None,
    decode_error: Exception | None = None,
) -> Mock:
    jwt_service = Mock(spec=JWTService)
    jwt_service.encode_jwt = Mock(return_value="access-token")
    jwt_service.decode_jwt = Mock(return_value=payload)

    if decode_error:
        jwt_service.decode_jwt.side_effect = decode_error

    return jwt_service


def make_user_service_mock(
    user: UserSchema | None = None,
    user_by_username: UserSchema | None = None,
) -> Mock:
    user_service = Mock(spec=UserService)
    user_service.get_by_id = AsyncMock(return_value=user)
    user_service.get_by_username = AsyncMock(return_value=user_by_username)
    user_service.create = AsyncMock(return_value=user)
    return user_service


def make_refresh_token_service_mock(
    refresh_token: RefreshTokenSchema | None = None,
    validated_token: uuid.UUID | None = None,
) -> Mock:
    refresh_token_service = Mock(spec=RefreshTokenService)
    refresh_token_service.create_token = AsyncMock(return_value=refresh_token or make_refresh_token_schema())
    refresh_token_service.validate_refresh_token_str = Mock(return_value=validated_token or uuid.uuid4())
    refresh_token_service.get_by_token = AsyncMock(return_value=refresh_token)
    refresh_token_service.delete_by_token = AsyncMock(return_value=None)
    return refresh_token_service


def make_cookies_service_mock(refresh_token_from_cookies: str | None = None) -> Mock:
    cookies_service = Mock(spec=CookiesService)
    cookies_service.set_cookies = Mock(return_value=None)
    cookies_service.delete_cookies = Mock(return_value=None)
    cookies_service.get_refresh_token_from_cookies = Mock(return_value=refresh_token_from_cookies or str(uuid.uuid4()))
    return cookies_service


def make_service(
    jwt_service: Mock | None = None,
    user_service: Mock | None = None,
    refresh_token_service: Mock | None = None,
    cookies_service: Mock | None = None,
) -> AuthService:
    return AuthService(
        jwt_service=cast(JWTService, jwt_service or make_jwt_service_mock()),
        user_service=cast(UserService, user_service or make_user_service_mock()),
        refresh_token_service=cast(RefreshTokenService, refresh_token_service or make_refresh_token_service_mock()),
        cookies_service=cast(CookiesService, cookies_service or make_cookies_service_mock()),
    )


async def create_user_from_create_data(user_create_data: UserCreateDatabaseSchema) -> UserSchema:
    return make_user_schema(
        username=user_create_data.username,
        password_hash=user_create_data.password_hash,
    )


async def test_register_user_creates_user_with_hashed_password() -> None:
    user_service = make_user_service_mock()
    user_service.create = AsyncMock(side_effect=create_user_from_create_data)
    service = make_service(user_service=user_service)
    user_create_data = UserCreateSchema(
        username="almaz",
        password="secret123",
        password_confirmation="secret123",
    )

    result = await service.register_user(user_create_data=user_create_data)

    user_service.get_by_username.assert_awaited_once_with(username=user_create_data.username)
    user_service.create.assert_awaited_once()
    created_user_data = user_service.create.await_args.kwargs["user_create_data"]
    assert isinstance(created_user_data, UserCreateDatabaseSchema)
    assert result.username == user_create_data.username
    assert created_user_data.username == user_create_data.username
    assert created_user_data.password_hash != user_create_data.password
    assert bcrypt.checkpw(
        user_create_data.password.encode("utf-8"),
        created_user_data.password_hash.encode("utf-8"),
    )


async def test_register_user_raises_error_when_username_exists() -> None:
    user = make_user_schema(username="almaz")
    user_service = make_user_service_mock(user_by_username=user)
    service = make_service(user_service=user_service)
    user_create_data = UserCreateSchema(
        username="almaz",
        password="secret123",
        password_confirmation="secret123",
    )

    with pytest.raises(UserAlreadyExistsHTTPException):
        await service.register_user(user_create_data=user_create_data)

    user_service.get_by_username.assert_awaited_once_with(username=user_create_data.username)
    user_service.create.assert_not_awaited()


async def test_authenticate_user_returns_access_token_and_sets_refresh_cookie() -> None:
    user = make_user_schema(password_hash=make_password_hash("secret123"))
    refresh_token = make_refresh_token_schema(user_id=user.id)
    jwt_service = make_jwt_service_mock()
    refresh_token_service = make_refresh_token_service_mock(refresh_token=refresh_token)
    cookies_service = make_cookies_service_mock()
    response = Response()
    service = make_service(
        jwt_service=jwt_service,
        user_service=make_user_service_mock(user_by_username=user),
        refresh_token_service=refresh_token_service,
        cookies_service=cookies_service,
    )

    result = await service.authenticate_user(
        login_data=UserLoginSchema(username=user.username, password="secret123"),
        response=response,
    )

    assert result.access_token == "access-token"
    jwt_service.encode_jwt.assert_called_once_with(payload=JWTPayloadSchema(sub=str(user.id), username=user.username))
    refresh_token_service.create_token.assert_awaited_once()
    refresh_token_create_data = refresh_token_service.create_token.await_args.kwargs["refresh_token_create_data"]
    assert isinstance(refresh_token_create_data, RefreshTokenCreateSchema)
    assert refresh_token_create_data.user_id == user.id
    cookies_service.set_cookies.assert_called_once_with(response=response, refresh_token=refresh_token)


async def test_authenticate_user_raises_error_for_wrong_password() -> None:
    user = make_user_schema(password_hash=make_password_hash("secret123"))
    jwt_service = make_jwt_service_mock()
    service = make_service(
        jwt_service=jwt_service,
        user_service=make_user_service_mock(user_by_username=user),
    )

    with pytest.raises(WrongUsernameOrPasswordHTTPException):
        await service.authenticate_user(
            login_data=UserLoginSchema(username=user.username, password="wrong-password"),
            response=Response(),
        )

    jwt_service.encode_jwt.assert_not_called()


async def test_authorize_user_returns_user_from_token_payload() -> None:
    user = make_user_schema()
    payload = JWTPayloadSchema(sub=str(user.id), username=user.username)
    user_service = make_user_service_mock(user=user)
    jwt_service = make_jwt_service_mock(payload=payload)
    service = make_service(jwt_service=jwt_service, user_service=user_service)

    result = await service.authorize_user(token="access-token")

    assert result == user
    jwt_service.decode_jwt.assert_called_once_with(token="access-token")
    user_service.get_by_id.assert_awaited_once_with(user_id=user.id)


async def test_authorize_user_raises_expired_token_error() -> None:
    jwt_service = make_jwt_service_mock(decode_error=ExpiredSignatureError())
    service = make_service(jwt_service=jwt_service)

    with pytest.raises(AccessTokenExpiredHTTPException):
        await service.authorize_user(token="access-token")

    jwt_service.decode_jwt.assert_called_once_with(token="access-token")


async def test_authorize_user_raises_invalid_token_error() -> None:
    jwt_service = make_jwt_service_mock(decode_error=InvalidTokenError())
    service = make_service(jwt_service=jwt_service)

    with pytest.raises(InvalidTokenHTTPException):
        await service.authorize_user(token="access-token")

    jwt_service.decode_jwt.assert_called_once_with(token="access-token")


async def test_authorize_websocket_user_maps_token_error_to_websocket_exception() -> None:
    jwt_service = make_jwt_service_mock(decode_error=InvalidTokenError())
    service = make_service(jwt_service=jwt_service)

    with pytest.raises(TokenIsInvalidOrExpiredWebSocketException):
        await service.authorize_websocket_user(token="access-token")

    jwt_service.decode_jwt.assert_called_once_with(token="access-token")


async def test_refresh_tokens_creates_new_access_token_for_valid_refresh_cookie() -> None:
    user = make_user_schema()
    refresh_token_value = uuid.uuid4()
    refresh_token = make_refresh_token_schema(user_id=user.id, refresh_token=refresh_token_value)
    jwt_service = make_jwt_service_mock()
    refresh_token_service = make_refresh_token_service_mock(
        refresh_token=refresh_token,
        validated_token=refresh_token_value,
    )
    cookies_service = make_cookies_service_mock(refresh_token_from_cookies=str(refresh_token_value))
    response = Response()
    service = make_service(
        jwt_service=jwt_service,
        user_service=make_user_service_mock(user=user),
        refresh_token_service=refresh_token_service,
        cookies_service=cookies_service,
    )

    result = await service.refresh_tokens(request=make_request(), response=response)

    assert result.access_token == "access-token"
    cookies_service.get_refresh_token_from_cookies.assert_called_once()
    refresh_token_service.validate_refresh_token_str.assert_called_once_with(refresh_token_str=str(refresh_token_value))
    refresh_token_service.get_by_token.assert_awaited_once_with(token=refresh_token_value)
    jwt_service.encode_jwt.assert_called_once_with(payload=JWTPayloadSchema(sub=str(user.id), username=user.username))
    cookies_service.set_cookies.assert_called_once_with(response=response, refresh_token=refresh_token)


async def test_refresh_tokens_raises_error_for_expired_refresh_token() -> None:
    user = make_user_schema()
    refresh_token_value = uuid.uuid4()
    expired_refresh_token = make_refresh_token_schema(
        user_id=user.id,
        refresh_token=refresh_token_value,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    refresh_token_service = make_refresh_token_service_mock(
        refresh_token=expired_refresh_token,
        validated_token=refresh_token_value,
    )
    service = make_service(
        user_service=make_user_service_mock(user=user),
        refresh_token_service=refresh_token_service,
        cookies_service=make_cookies_service_mock(refresh_token_from_cookies=str(refresh_token_value)),
    )

    with pytest.raises(RefreshTokenExpiredHTTPException):
        await service.refresh_tokens(request=make_request(), response=Response())

    refresh_token_service.create_token.assert_not_awaited()


async def test_logout_user_deletes_refresh_token_and_cookies() -> None:
    refresh_token_value = uuid.uuid4()
    refresh_token_service = make_refresh_token_service_mock(validated_token=refresh_token_value)
    cookies_service = make_cookies_service_mock(refresh_token_from_cookies=str(refresh_token_value))
    response = Response()
    service = make_service(refresh_token_service=refresh_token_service, cookies_service=cookies_service)

    await service.logout_user(request=make_request(), response=response)

    cookies_service.get_refresh_token_from_cookies.assert_called_once()
    refresh_token_service.validate_refresh_token_str.assert_called_once_with(refresh_token_str=str(refresh_token_value))
    refresh_token_service.delete_by_token.assert_awaited_once_with(token=refresh_token_value)
    cookies_service.delete_cookies.assert_called_once_with(response=response)
