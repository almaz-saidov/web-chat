from functools import lru_cache

from fastapi import Request, Response

from core.config import settings
from core.exceptions import RefreshTokenCookieIsMissingHTTPException
from database.models import RefreshToken


class CookiesService:
    def set_cookies(self, response: Response, refresh_token: RefreshToken) -> None:
        response.set_cookie(
            key="refresh_token",
            value=str(refresh_token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/auth",
        )

    def get_refresh_token_from_cookies(self, request: Request) -> str:
        refresh_token_str = request.cookies.get("refresh_token")

        if not refresh_token_str:
            raise RefreshTokenCookieIsMissingHTTPException()

        return refresh_token_str


@lru_cache
def get_cookies_service() -> CookiesService:
    return CookiesService()
