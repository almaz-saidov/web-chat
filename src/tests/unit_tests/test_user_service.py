import uuid
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from core.exceptions import UserNotFoundHTTPException
from database.repositories.user import UserRepository
from schemas.user import UserCreateDatabaseSchema, UserSchema
from services.user import UserService


def make_user_schema(
    user_id: uuid.UUID | None = None,
    username: str = "almaz",
    password_hash: str = "password-hash",
) -> UserSchema:
    return UserSchema(
        id=user_id or uuid.uuid4(),
        username=username,
        password_hash=password_hash,
        created_at=datetime.now(timezone.utc),
    )


def make_repository() -> Mock:
    return Mock(spec=UserRepository)


def make_service(repository: Mock) -> UserService:
    return UserService(repository=cast(UserRepository, repository))


async def test_get_by_id_returns_user_when_user_exists() -> None:
    user = make_user_schema()
    repository = make_repository()
    repository.get_by_id = AsyncMock(return_value=user)
    service = make_service(repository=repository)

    result = await service.get_by_id(user_id=user.id)

    assert result == user, "UserService.get_by_id must return user found by repository"
    repository.get_by_id.assert_awaited_once_with(user_id=user.id)


async def test_get_by_id_raises_error_when_user_does_not_exist() -> None:
    user_id = uuid.uuid4()
    repository = make_repository()
    repository.get_by_id = AsyncMock(return_value=None)
    service = make_service(repository=repository)

    with pytest.raises(UserNotFoundHTTPException):
        await service.get_by_id(user_id=user_id)

    repository.get_by_id.assert_awaited_once_with(user_id=user_id)


async def test_get_by_username_returns_repository_result() -> None:
    user = make_user_schema(username="almaz")
    repository = make_repository()
    repository.get_by_username = AsyncMock(return_value=user)
    service = make_service(repository=repository)

    result = await service.get_by_username(username="almaz")

    assert result == user, "UserService.get_by_username must return repository result"
    repository.get_by_username.assert_awaited_once_with(username="almaz")


async def test_create_returns_created_user() -> None:
    user_create_data = UserCreateDatabaseSchema(
        username="almaz", password_hash="password-hash"
    )
    created_user = make_user_schema(
        username=user_create_data.username,
        password_hash=user_create_data.password_hash,
    )
    repository = make_repository()
    repository.create = AsyncMock(return_value=created_user)
    service = make_service(repository=repository)

    result = await service.create(user_create_data=user_create_data)

    assert result == created_user, (
        "UserService.create must return user created by repository"
    )
    repository.create.assert_awaited_once_with(user_create_data=user_create_data)
