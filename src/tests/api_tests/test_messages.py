import uuid
from typing import cast

from fastapi import status
from httpx import AsyncClient, Response

DEFAULT_PASSWORD = "secret123"


def make_username(prefix: str = "message_user") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def make_signature_sample() -> dict[str, object]:
    return {
        "points": [
            {"x": 0, "y": 0, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 0},
            {"x": 1, "y": 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 50},
            {"x": 2, "y": 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 100},
            {"x": 3, "y": 2, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 150},
            {"x": 4, "y": 3, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 200},
        ],
        "duration_ms": 200,
        "break_count": 0,
    }


def make_signature_samples() -> list[dict[str, object]]:
    return [make_signature_sample() for _ in range(5)]


def make_register_payload(
    username: str | None = None, password: str = DEFAULT_PASSWORD
) -> dict[str, object]:
    return {
        "username": username or make_username(),
        "password": password,
        "password_confirmation": password,
        "signature_samples": make_signature_samples(),
    }


def assert_response_detail(response: Response, expected_detail: str) -> None:
    response_data = response.json()

    assert isinstance(response_data, dict), "Error response must be a JSON object"
    assert response_data.get("detail") == expected_detail, (
        "Error response must contain expected detail"
    )


async def get_access_token(
    async_client: AsyncClient, username: str | None = None
) -> tuple[str, str]:
    payload = make_register_payload(username=username)
    register_response = await async_client.post("/api/auth/register", json=payload)
    assert register_response.status_code == status.HTTP_201_CREATED, (
        "Access token helper must register user"
    )

    login_response = await async_client.post(
        "/api/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
            "signature_sample": make_signature_sample(),
        },
    )
    assert login_response.status_code == status.HTTP_200_OK, (
        "Access token helper must authenticate user"
    )

    response_data = login_response.json()
    assert isinstance(response_data, dict), (
        "Login helper response must be a JSON object"
    )
    access_token = response_data.get("access_token")
    assert isinstance(access_token, str), (
        "Login helper response must contain string access token"
    )

    return cast(str, payload["username"]), access_token


def make_auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def test_get_messages_returns_401_without_token(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/messages")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Messages endpoint must require bearer token"
    )
    assert_response_detail(response=response, expected_detail="Not authenticated")


async def test_get_messages_returns_200_for_authorized_user(
    async_client: AsyncClient,
) -> None:
    _, access_token = await get_access_token(async_client=async_client)

    response = await async_client.get(
        "/api/messages", headers=make_auth_headers(access_token=access_token)
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Messages endpoint must return 200 for authorized user"
    )
    response_data = response.json()
    assert isinstance(response_data, list), "Messages endpoint must return a JSON list"


async def test_get_messages_returns_401_for_invalid_token(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/api/messages", headers=make_auth_headers(access_token="invalid-token")
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Messages endpoint must reject invalid bearer token"
    )
    assert_response_detail(response=response, expected_detail="Invalid token")


async def test_create_message_returns_401_without_token(
    async_client: AsyncClient,
) -> None:
    response = await async_client.post("/api/messages", json={"content": "hello"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "Create message endpoint must require bearer token"
    )
    assert_response_detail(response=response, expected_detail="Not authenticated")


async def test_create_message_returns_200_for_authorized_user(
    async_client: AsyncClient,
) -> None:
    username, access_token = await get_access_token(async_client=async_client)
    message_content = f"hello-{uuid.uuid4().hex}"

    response = await async_client.post(
        "/api/messages",
        json={"content": message_content},
        headers=make_auth_headers(access_token=access_token),
    )

    assert response.status_code == status.HTTP_200_OK, (
        "Create message endpoint must return 200 for authorized user"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), (
        "Create message response must be a JSON object"
    )
    assert response_data.get("username") == username, (
        "Create message response must contain message author username"
    )
    assert response_data.get("content") == message_content, (
        "Create message response must contain submitted content"
    )
    assert "id" in response_data, "Create message response must contain message id"
    assert "created_at" in response_data, (
        "Create message response must contain message creation timestamp"
    )


async def test_create_message_returns_422_for_invalid_payload(
    async_client: AsyncClient,
) -> None:
    _, access_token = await get_access_token(async_client=async_client)

    response = await async_client.post(
        "/api/messages",
        json={},
        headers=make_auth_headers(access_token=access_token),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Create message endpoint must validate payload"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), (
        "Validation error response must be a JSON object"
    )
    assert "detail" in response_data, "Validation error response must contain detail"
