import uuid
from typing import cast

from fastapi import status
from httpx import AsyncClient, Response

DEFAULT_PASSWORD = "secret123"


def make_username(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def make_signature_sample(y_offset: float = 0) -> dict[str, object]:
    return {
        "points": [
            {"x": 0, "y": y_offset, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 0},
            {"x": 1, "y": y_offset + 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 50},
            {"x": 2, "y": y_offset + 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 100},
            {"x": 3, "y": y_offset + 2, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 150},
            {"x": 4, "y": y_offset + 3, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 200},
        ],
        "duration_ms": 200,
        "break_count": 0,
    }


def make_wrong_signature_sample() -> dict[str, object]:
    return {
        "points": [
            {"x": 0, "y": 0, "pressure": 1, "tilt_x": 80, "tilt_y": -80, "time_ms": 0},
            {"x": 0, "y": 4, "pressure": 1, "tilt_x": 80, "tilt_y": -80, "time_ms": 400},
            {"x": 4, "y": 0, "pressure": 1, "tilt_x": 80, "tilt_y": -80, "time_ms": 800},
            {"x": 4, "y": 4, "pressure": 1, "tilt_x": 80, "tilt_y": -80, "time_ms": 1200},
            {"x": 2, "y": 2, "pressure": 1, "tilt_x": 80, "tilt_y": -80, "time_ms": 1600},
        ],
        "duration_ms": 1600,
        "break_count": 4,
    }


def make_short_signature_sample() -> dict[str, object]:
    return {
        "points": [
            {"x": 0, "y": 0, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 0},
            {"x": 1, "y": 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 50},
            {"x": 2, "y": 1, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 100},
            {"x": 3, "y": 2, "pressure": 0.5, "tilt_x": 0, "tilt_y": 0, "time_ms": 150},
        ],
        "duration_ms": 150,
        "break_count": 0,
    }


def make_signature_samples() -> list[dict[str, object]]:
    return [make_signature_sample(y_offset=0) for _ in range(5)]


def make_register_payload(username: str | None = None, password: str = DEFAULT_PASSWORD) -> dict[str, object]:
    return {
        "username": username or make_username(),
        "password": password,
        "password_confirmation": password,
        "signature_samples": make_signature_samples(),
    }


def assert_response_detail(response: Response, expected_detail: str) -> None:
    response_data = response.json()

    assert isinstance(response_data, dict), "Error response must be a JSON object"
    assert response_data.get("detail") == expected_detail, "Error response must contain expected detail"


async def register_user(async_client: AsyncClient, payload: dict[str, object]) -> Response:
    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, "Register helper must create user successfully"
    return response


async def login_user(async_client: AsyncClient, username: str, password: str = DEFAULT_PASSWORD) -> Response:
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
            "signature_sample": make_signature_sample(),
        },
    )

    assert response.status_code == status.HTTP_200_OK, "Login helper must authenticate user successfully"
    return response


def assert_access_token_response(response: Response, failure_message_prefix: str) -> None:
    response_data = response.json()

    assert isinstance(response_data, dict), f"{failure_message_prefix} response must be a JSON object"
    assert "access_token" in response_data, f"{failure_message_prefix} response must contain access token"
    assert response_data.get("token_type") == "Bearer", f"{failure_message_prefix} response must use Bearer token type"
    assert isinstance(response_data["access_token"], str), f"{failure_message_prefix} access token must be a string"
    assert response_data["access_token"], f"{failure_message_prefix} access token must not be empty"


def assert_refresh_cookie_set(response: Response) -> None:
    set_cookie_header = response.headers.get("set-cookie")

    assert set_cookie_header is not None, "Login response must set refresh token cookie"
    assert "refresh_token=" in set_cookie_header, "Refresh token cookie must be present in Set-Cookie header"
    assert "HttpOnly" in set_cookie_header, "Refresh token cookie must be HttpOnly"


def get_refresh_cookie_headers(response: Response) -> dict[str, str]:
    refresh_token = response.cookies.get("refresh_token")

    assert refresh_token is not None, "Login response cookies must contain refresh token"
    return {"Cookie": f"refresh_token={refresh_token}"}


async def test_register_returns_201_for_valid_payload(async_client: AsyncClient) -> None:
    payload = make_register_payload()

    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, "Register endpoint must return 201 for valid payload"
    response_data = response.json()
    assert isinstance(response_data, dict), "Register response must be a JSON object"
    assert response_data.get("username") == payload["username"], "Register response must contain created username"
    assert "id" in response_data, "Register response must contain user id"
    assert "created_at" in response_data, "Register response must contain user creation timestamp"
    assert "password_hash" not in response_data, "Register response must not expose password hash"


async def test_register_returns_409_for_duplicate_username(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)

    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT, "Register endpoint must reject duplicate username"
    assert_response_detail(response=response, expected_detail="The user with this username already exists")


async def test_register_returns_422_for_invalid_payload(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/auth/register",
        json={
            "username": "ab",
            "password": "short",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, "Register endpoint must validate payload"
    response_data = response.json()
    assert isinstance(response_data, dict), "Validation error response must be a JSON object"
    assert "detail" in response_data, "Validation error response must contain detail"


async def test_register_returns_422_for_wrong_signature_sample_count(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    payload["signature_samples"] = make_signature_samples()[:-1]

    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Register endpoint must validate signature sample count"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), "Validation error response must be a JSON object"
    assert "detail" in response_data, "Validation error response must contain detail"


async def test_register_returns_422_for_short_signature_sample(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    payload["signature_samples"] = [make_short_signature_sample() for _ in range(5)]

    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Register endpoint must validate signature sample point count"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), "Validation error response must be a JSON object"
    assert "detail" in response_data, "Validation error response must contain detail"


async def test_login_returns_200_and_refresh_cookie_for_valid_credentials(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)

    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
            "signature_sample": make_signature_sample(),
        },
    )

    assert response.status_code == status.HTTP_200_OK, "Login endpoint must return 200 for valid credentials"
    assert_access_token_response(response=response, failure_message_prefix="Login")
    assert_refresh_cookie_set(response=response)


async def test_login_returns_422_without_signature_sample(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": make_username(),
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, "Login endpoint must require signature sample"
    response_data = response.json()
    assert isinstance(response_data, dict), "Validation error response must be a JSON object"
    assert "detail" in response_data, "Validation error response must contain detail"


async def test_login_returns_422_for_short_signature_sample(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": make_username(),
            "password": DEFAULT_PASSWORD,
            "signature_sample": make_short_signature_sample(),
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        "Login endpoint must validate signature sample point count"
    )
    response_data = response.json()
    assert isinstance(response_data, dict), "Validation error response must be a JSON object"
    assert "detail" in response_data, "Validation error response must contain detail"


async def test_login_returns_401_for_wrong_password(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)

    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": payload["username"],
            "password": "wrong-password",
            "signature_sample": make_signature_sample(),
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, "Login endpoint must reject wrong password"
    assert_response_detail(response=response, expected_detail="Wrong username or password")


async def test_login_returns_401_for_wrong_signature(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)

    response = await async_client.post(
        "/api/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
            "signature_sample": make_wrong_signature_sample(),
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, "Login endpoint must reject wrong signature"
    assert_response_detail(response=response, expected_detail="Signature verification failed")


async def test_refresh_returns_200_for_valid_refresh_cookie(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    login_response = await login_user(
        async_client=async_client,
        username=cast(str, payload["username"]),
        password=cast(str, payload["password"]),
    )

    response = await async_client.post("/api/auth/refresh", headers=get_refresh_cookie_headers(response=login_response))

    assert response.status_code == status.HTTP_200_OK, "Refresh endpoint must return 200 with valid refresh cookie"
    assert_access_token_response(response=response, failure_message_prefix="Refresh")
    assert_refresh_cookie_set(response=response)


async def test_refresh_returns_401_without_refresh_cookie(async_client: AsyncClient) -> None:
    response = await async_client.post("/api/auth/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, "Refresh endpoint must require refresh token cookie"
    assert_response_detail(response=response, expected_detail="Refresh token cookie is missing")


async def test_logout_returns_200_and_deletes_refresh_cookie(async_client: AsyncClient) -> None:
    payload = make_register_payload()
    await register_user(async_client=async_client, payload=payload)
    login_response = await login_user(
        async_client=async_client,
        username=cast(str, payload["username"]),
        password=cast(str, payload["password"]),
    )

    response = await async_client.post("/api/auth/logout", headers=get_refresh_cookie_headers(response=login_response))

    assert response.status_code == status.HTTP_200_OK, "Logout endpoint must return 200 for valid refresh cookie"
    set_cookie_header = response.headers.get("set-cookie")
    assert set_cookie_header is not None, "Logout response must include Set-Cookie header"
    assert "refresh_token=" in set_cookie_header, "Logout response must target refresh token cookie"
    assert "Max-Age=0" in set_cookie_header, "Logout response must expire refresh token cookie immediately"
