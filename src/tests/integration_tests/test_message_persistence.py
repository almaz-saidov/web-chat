import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import status
from httpx import AsyncClient, Response
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message, User

DEFAULT_PASSWORD = "secret123"


def make_username(prefix: str = "message_user") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def make_register_payload(
    username: str | None = None, password: str = DEFAULT_PASSWORD
) -> dict[str, str]:
    return {
        "username": username or make_username(),
        "password": password,
        "password_confirmation": password,
    }


def make_auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def register_user(async_client: AsyncClient, payload: dict[str, str]) -> Response:
    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, (
        "Register helper must create user successfully"
    )
    return response


async def login_user(
    async_client: AsyncClient, username: str, password: str = DEFAULT_PASSWORD
) -> str:
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Login helper must authenticate user successfully"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), (
        "Login helper response must be a JSON object"
    )
    assert isinstance(response_data.get("access_token"), str), (
        "Login helper response must contain string access token"
    )
    return response_data["access_token"]


async def get_user_by_username(db_session: AsyncSession, username: str) -> User:
    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    assert user is not None, "User must exist in database"
    return user


async def create_authorized_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> tuple[User, str]:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    access_token = await login_user(
        async_client=async_client,
        username=payload["username"],
        password=payload["password"],
    )
    user = await get_user_by_username(
        db_session=db_session, username=payload["username"]
    )

    return user, access_token


def get_response_data(response: Response) -> dict[str, Any]:
    response_data = response.json()

    assert isinstance(response_data, dict), "Response body must be a JSON object"
    return response_data


def get_response_list(response: Response) -> list[Any]:
    response_data = response.json()

    assert isinstance(response_data, list), "Response body must be a JSON list"
    return response_data


async def test_create_message_persists_database_row_for_authorized_user(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user, access_token = await create_authorized_user(
        async_client=async_client, db_session=db_session
    )
    message_content = f"integration-message-{uuid.uuid4().hex}"

    response = await async_client.post(
        "/api/message/create",
        json={"content": message_content},
        headers=make_auth_headers(access_token=access_token),
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Create message endpoint must accept authorized user"
    )
    response_data = get_response_data(response=response)
    assert isinstance(response_data.get("id"), str), (
        "Create message response must contain message id"
    )

    message_id = uuid.UUID(response_data["id"])
    result = await db_session.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    assert message is not None, "Create message endpoint must persist message row"
    assert message.user_id == user.id, (
        "Persisted message must belong to authorized user"
    )
    assert message.content == message_content, (
        "Persisted message content must match submitted content"
    )


async def test_get_messages_reads_persisted_rows_in_created_at_order(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user, access_token = await create_authorized_user(
        async_client=async_client, db_session=db_session
    )
    first_content = f"first-integration-message-{uuid.uuid4().hex}"
    second_content = f"second-integration-message-{uuid.uuid4().hex}"
    first_created_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    second_created_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    await db_session.execute(
        insert(Message).values(
            user_id=user.id, content=second_content, created_at=second_created_at
        )
    )
    await db_session.execute(
        insert(Message).values(
            user_id=user.id, content=first_content, created_at=first_created_at
        )
    )
    await db_session.commit()

    response = await async_client.get(
        "/api/message/all", headers=make_auth_headers(access_token=access_token)
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Messages endpoint must return persisted history"
    )
    response_data = get_response_list(response=response)
    target_contents = {first_content, second_content}
    persisted_messages = [
        message_data
        for message_data in response_data
        if isinstance(message_data, dict)
        and message_data.get("content") in target_contents
    ]
    assert [message_data["content"] for message_data in persisted_messages] == [
        first_content,
        second_content,
    ], "Messages endpoint must return persisted messages ordered by creation time"
    assert all(
        message_data.get("username") == user.username
        for message_data in persisted_messages
    ), "Messages endpoint must return author username for persisted messages"
