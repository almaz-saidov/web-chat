import uuid
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from core.exceptions import (
    InvalidRefreshTokenFormatHTTPException,
    InvalidTokenHTTPException,
)
from database.repositories.refresh_token_repository import RefreshTokenRepository
from schemas.refresh_token import RefreshTokenCreateSchema, RefreshTokenSchema
from services.refresh_token_service import RefreshTokenService


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
        expires_at=expires_at or datetime.now(timezone.utc),
    )


def make_repository() -> Mock:
    return Mock(spec=RefreshTokenRepository)


def make_service(repository: Mock) -> RefreshTokenService:
    return RefreshTokenService(repository=cast(RefreshTokenRepository, repository))


def test_validate_refresh_token_str_returns_uuid_for_valid_value() -> None:
    service = make_service(repository=make_repository())
    token = uuid.uuid4()

    result = service.validate_refresh_token_str(refresh_token_str=str(token))

    assert result == token, "Valid refresh token string must be converted to UUID"


def test_validate_refresh_token_str_raises_error_for_invalid_value() -> None:
    service = make_service(repository=make_repository())

    with pytest.raises(InvalidRefreshTokenFormatHTTPException):
        service.validate_refresh_token_str(refresh_token_str="not-a-uuid")


async def test_get_by_token_returns_refresh_token_when_it_exists() -> None:
    refresh_token = make_refresh_token_schema()
    repository = make_repository()
    repository.get_by_token = AsyncMock(return_value=refresh_token)
    service = make_service(repository=repository)

    result = await service.get_by_token(token=refresh_token.refresh_token)

    assert result == refresh_token, (
        "RefreshTokenService must return refresh token found by repository"
    )
    repository.get_by_token.assert_awaited_once_with(token=refresh_token.refresh_token)


async def test_get_by_token_raises_error_when_token_does_not_exist() -> None:
    token = uuid.uuid4()
    repository = make_repository()
    repository.get_by_token = AsyncMock(return_value=None)
    service = make_service(repository=repository)

    with pytest.raises(InvalidTokenHTTPException):
        await service.get_by_token(token=token)

    repository.get_by_token.assert_awaited_once_with(token=token)


async def test_create_token_deletes_existing_token_for_user_before_create() -> None:
    user_id = uuid.uuid4()
    existing_token = make_refresh_token_schema(user_id=user_id)
    create_data = RefreshTokenCreateSchema(
        user_id=user_id, expires_at=datetime.now(timezone.utc)
    )
    created_token = make_refresh_token_schema(
        user_id=user_id, expires_at=create_data.expires_at
    )
    repository = make_repository()
    repository.get_by_user_id = AsyncMock(return_value=existing_token)
    repository.force_delete_by_user_id = AsyncMock(return_value=None)
    repository.create = AsyncMock(return_value=created_token)
    service = make_service(repository=repository)

    result = await service.create_token(refresh_token_create_data=create_data)

    assert result == created_token, (
        "RefreshTokenService.create_token must return token created by repository"
    )
    repository.get_by_user_id.assert_awaited_once_with(user_id=user_id)
    repository.force_delete_by_user_id.assert_awaited_once_with(user_id=user_id)
    repository.create.assert_awaited_once_with(refresh_token_create_data=create_data)


async def test_delete_by_token_deletes_token_in_repository() -> None:
    repository = make_repository()
    repository.force_delete_by_token = AsyncMock(return_value=None)
    service = make_service(repository=repository)
    token = uuid.uuid4()

    await service.delete_by_token(token=token)

    repository.force_delete_by_token.assert_awaited_once_with(token=token)
