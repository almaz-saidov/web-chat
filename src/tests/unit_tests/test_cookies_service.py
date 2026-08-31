import uuid
from datetime import datetime, timezone

import pytest
from fastapi import Request, Response

from core.exceptions import RefreshTokenCookieIsMissingHTTPException
from schemas.refresh_token import RefreshTokenSchema
from services.cookies import CookiesService


def make_refresh_token_schema(
    refresh_token: uuid.UUID | None = None,
) -> RefreshTokenSchema:
    return RefreshTokenSchema(
        id=1,
        user_id=uuid.uuid4(),
        refresh_token=refresh_token or uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )


def make_request(cookie_header: bytes | None = None) -> Request:
    headers = []
    if cookie_header:
        headers.append((b"cookie", cookie_header))

    return Request({"type": "http", "headers": headers})


def test_set_cookies_sets_refresh_token_cookie() -> None:
    service = CookiesService()
    response = Response()
    refresh_token = make_refresh_token_schema()

    service.set_cookies(response=response, refresh_token=refresh_token)

    cookie = response.headers["set-cookie"]
    assert f"refresh_token={refresh_token.refresh_token}" in cookie, (
        "Refresh token cookie must contain token value"
    )
    assert "HttpOnly" in cookie, "Refresh token cookie must be HttpOnly"
    assert "Secure" in cookie, "Refresh token cookie must be Secure"
    assert "Path=/api/auth" in cookie, (
        "Refresh token cookie must be scoped to auth path"
    )


def test_delete_cookies_expires_refresh_token_cookie() -> None:
    service = CookiesService()
    response = Response()

    service.delete_cookies(response=response)

    cookie = response.headers["set-cookie"]
    assert "refresh_token=" in cookie, "Delete cookies must target refresh token cookie"
    assert "Max-Age=0" in cookie, (
        "Delete cookies must expire refresh token cookie immediately"
    )
    assert "Path=/api/auth" in cookie, "Delete cookies must use the auth cookie path"


def test_get_refresh_token_from_cookies_returns_cookie_value() -> None:
    service = CookiesService()
    refresh_token = uuid.uuid4()
    request = make_request(cookie_header=f"refresh_token={refresh_token}".encode())

    result = service.get_refresh_token_from_cookies(request=request)

    assert result == str(refresh_token), (
        "CookiesService must return refresh token value from request cookies"
    )


def test_get_refresh_token_from_cookies_raises_error_when_cookie_is_missing() -> None:
    service = CookiesService()
    request = make_request()

    with pytest.raises(RefreshTokenCookieIsMissingHTTPException):
        service.get_refresh_token_from_cookies(request=request)
