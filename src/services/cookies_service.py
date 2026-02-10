from functools import lru_cache

from fastapi import Response

from core.config import settings
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


@lru_cache
def get_cookies_service() -> CookiesService:
    return CookiesService()
