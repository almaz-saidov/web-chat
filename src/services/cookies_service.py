from fastapi import Request, Response

from core.config import settings
from core.exceptions import RefreshTokenCookieIsMissingHTTPException
from schemas.refresh_token import RefreshTokenSchema


class CookiesService:
    def set_cookies(self, response: Response, refresh_token: RefreshTokenSchema) -> None:
        response.set_cookie(
            key="refresh_token",
            value=str(refresh_token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/auth",
        )

    def delete_cookies(self, response: Response) -> None:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="lax",
            path="/api/auth",
        )

    def get_refresh_token_from_cookies(self, request: Request) -> str:
        refresh_token_str = request.cookies.get("refresh_token")

        if not refresh_token_str:
            raise RefreshTokenCookieIsMissingHTTPException()

        return refresh_token_str


def get_cookies_service() -> CookiesService:
    return CookiesService()
