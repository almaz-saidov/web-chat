import uuid

import bcrypt
from fastapi import status
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RefreshToken, User

DEFAULT_PASSWORD = "secret123"


def make_username(prefix: str = "integration_user") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def make_register_payload(username: str | None = None, password: str = DEFAULT_PASSWORD) -> dict[str, str]:
    return {
        "username": username or make_username(),
        "password": password,
        "password_confirmation": password,
    }


def get_refresh_token_from_response(response: Response) -> uuid.UUID:
    refresh_token = response.cookies.get("refresh_token")

    assert refresh_token is not None, "Auth response must contain refresh token cookie"
    return uuid.UUID(refresh_token)


def make_refresh_cookie_headers(refresh_token: uuid.UUID) -> dict[str, str]:
    return {"Cookie": f"refresh_token={refresh_token}"}


async def register_user(async_client: AsyncClient, payload: dict[str, str]) -> Response:
    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, "Register helper must create user successfully"
    return response


async def login_user(async_client: AsyncClient, username: str, password: str = DEFAULT_PASSWORD) -> Response:
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_200_OK, "Login helper must authenticate user successfully"
    return response


async def get_user_by_username(db_session: AsyncSession, username: str) -> User:
    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    assert user is not None, "User must exist in database"
    return user


async def get_refresh_tokens_by_user_id(db_session: AsyncSession, user_id: uuid.UUID) -> list[RefreshToken]:
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
    return list(result.scalars().all())


async def test_register_persists_user_with_hashed_password(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = make_register_payload()

    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, "Register endpoint must create user"
    user = await get_user_by_username(db_session=db_session, username=payload["username"])
    assert user.username == payload["username"], "Persisted user must keep registered username"
    assert user.password_hash != payload["password"], "Persisted user password must not be stored as plain text"
    assert bcrypt.checkpw(
        payload["password"].encode("utf-8"),
        user.password_hash.encode("utf-8"),
    ), "Persisted user password hash must match original password"


async def test_login_persists_refresh_token_matching_cookie(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    user = await get_user_by_username(db_session=db_session, username=payload["username"])

    response = await login_user(
        async_client=async_client,
        username=payload["username"],
        password=payload["password"],
    )

    refresh_token = get_refresh_token_from_response(response=response)
    refresh_tokens = await get_refresh_tokens_by_user_id(db_session=db_session, user_id=user.id)
    assert len(refresh_tokens) == 1, "Login must persist exactly one refresh token for user"
    assert refresh_tokens[0].refresh_token == refresh_token, "Persisted refresh token must match response cookie"
    assert refresh_tokens[0].user_id == user.id, "Persisted refresh token must belong to authenticated user"


async def test_refresh_replaces_refresh_token_in_database(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    user = await get_user_by_username(db_session=db_session, username=payload["username"])
    login_response = await login_user(
        async_client=async_client,
        username=payload["username"],
        password=payload["password"],
    )
    original_refresh_token = get_refresh_token_from_response(response=login_response)

    response = await async_client.post(
        "/api/auth/refresh",
        headers=make_refresh_cookie_headers(refresh_token=original_refresh_token),
    )

    assert response.status_code == status.HTTP_200_OK, "Refresh endpoint must accept valid refresh token"
    new_refresh_token = get_refresh_token_from_response(response=response)
    refresh_tokens = await get_refresh_tokens_by_user_id(db_session=db_session, user_id=user.id)
    assert len(refresh_tokens) == 1, "Refresh endpoint must keep exactly one active refresh token for user"
    assert refresh_tokens[0].refresh_token == new_refresh_token, "Database must contain newly issued refresh token"
    assert refresh_tokens[0].refresh_token != original_refresh_token, "Refresh endpoint must replace old refresh token"


async def test_logout_deletes_refresh_token_from_database(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    user = await get_user_by_username(db_session=db_session, username=payload["username"])
    login_response = await login_user(
        async_client=async_client,
        username=payload["username"],
        password=payload["password"],
    )
    refresh_token = get_refresh_token_from_response(response=login_response)

    response = await async_client.post(
        "/api/auth/logout",
        headers=make_refresh_cookie_headers(refresh_token=refresh_token),
    )

    assert response.status_code == status.HTTP_200_OK, "Logout endpoint must accept valid refresh token"
    refresh_tokens = await get_refresh_tokens_by_user_id(db_session=db_session, user_id=user.id)
    assert refresh_tokens == [], "Logout endpoint must delete persisted refresh token"
