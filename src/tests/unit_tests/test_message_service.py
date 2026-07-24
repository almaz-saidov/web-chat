import uuid
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

from database.repositories.message_repository import MessageRepository
from schemas.message import MessageCreateSchema, MessageSchema
from schemas.user import UserSchema
from services.message_service import MessageService


def make_user_schema() -> UserSchema:
    return UserSchema(
        id=uuid.uuid4(),
        username="almaz",
        password_hash="password-hash",
        created_at=datetime.now(timezone.utc),
    )


def make_message_schema(content: str = "hello") -> MessageSchema:
    return MessageSchema(
        id=uuid.uuid4(),
        username="almaz",
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def make_repository() -> Mock:
    return Mock(spec=MessageRepository)


def make_service(repository: Mock) -> MessageService:
    return MessageService(repository=cast(MessageRepository, repository))


async def test_get_all_returns_repository_messages() -> None:
    messages = [
        make_message_schema(content="first"),
        make_message_schema(content="second"),
    ]
    repository = make_repository()
    repository.get_all = AsyncMock(return_value=messages)
    service = make_service(repository=repository)

    result = await service.get_all()

    assert result == messages, (
        "MessageService.get_all must return messages from repository"
    )
    repository.get_all.assert_awaited_once_with()


async def test_create_returns_created_message() -> None:
    user = make_user_schema()
    message_create_data = MessageCreateSchema(content="hello")
    created_message = make_message_schema(content=message_create_data.content)
    repository = make_repository()
    repository.create = AsyncMock(return_value=created_message)
    service = make_service(repository=repository)

    result = await service.create(message_create_data=message_create_data, user=user)

    assert result == created_message, (
        "MessageService.create must return the message created by repository"
    )
    repository.create.assert_awaited_once_with(
        message_create_data=message_create_data, user=user
    )
