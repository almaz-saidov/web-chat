import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import bcrypt
from fastapi import Depends, Request, Response
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from api.schemas import (AccessTokenSchema, LocalStorageUserSchema,
                         UserCreateSchema, UserLoginSchema)
from core.exceptions import (AccessTokenExpiredHTTPException,
                             InvalidTokenHTTPException,
                             RefreshTokenExpiredHTTPException,
                             UserAlreadyExistsHTTPException,
                             WrongRefreshTokenHTTPException,
                             WrongUsernameOrPasswordHTTPException)
from database.models import User
from services.cookies_service import CookiesService, get_cookies_service
from services.jwt_service import JWTService, get_jwt_service
from services.refresh_token_service import (RefreshTokenService,
                                            get_refresh_token_service)
from services.user_service import UserService, get_user_service


class AuthService:
    def __init__(
        self,
        jwt_service: JWTService,
        user_service: UserService,
        refresh_token_service: RefreshTokenService,
        cookies_service: CookiesService,
    ) -> None:
        self.__jwt_service = jwt_service
        self.__user_service = user_service
        self.__refresh_token_service = refresh_token_service
        self.__cookies_service = cookies_service

    async def register_user(self, user_data: UserCreateSchema) -> User:
        user = await self._get_user(username=user_data.username)
        if user:
            raise UserAlreadyExistsHTTPException()

        return await self._register_user_in_db(user_data)

    async def authenticate_user(self, login_data: UserLoginSchema, response: Response) -> AccessTokenSchema:
        user = await self._get_user(username=login_data.username)
        if not user or not self._verify_password(login_data.password, user.password_hash):
            raise WrongUsernameOrPasswordHTTPException()

        access_token = await self._create_tokens(user, response)

        return AccessTokenSchema(access_token=access_token)

    async def authorize_user(self, token: str) -> User:
        try:
            payload = self.__jwt_service.decode_jwt(token)
        except ExpiredSignatureError:
            raise AccessTokenExpiredHTTPException()
        except InvalidTokenError:
            raise InvalidTokenHTTPException()

        user = await self._get_user_via_payload(payload)
        return user

    async def refresh_tokens(self, user_data: LocalStorageUserSchema, request: Request, response: Response) -> AccessTokenSchema:
        refresh_token_from_cookies_str = self.__cookies_service.get_refresh_token_from_cookies(request)
        refresh_token_from_cookies = self.__refresh_token_service.validate_refresh_token_str(refresh_token_from_cookies_str)

        await self._validate_refresh_token(refresh_token_from_cookies)

        user = await self._get_user(username=user_data.username)
        access_token = await self._create_tokens(user, response)

        return AccessTokenSchema(access_token=access_token)

    async def _create_tokens(self, user: User, response: Response) -> str:
        jwt_payload = self._get_jwt_payload(user)
        access_token = self.__jwt_service.encode_jwt(jwt_payload)

        refresh_token_creation_data = self._get_refresh_token_creation_data(user)
        refresh_token = await self.__refresh_token_service.create_token(refresh_token_creation_data)
        self.__cookies_service.set_cookies(response, refresh_token)

        return access_token

    async def _get_user_via_payload(self, payload: dict[str, Any]) -> User:
        user_id = uuid.UUID(payload.get("sub"))
        username: str = payload.get("username")

        user = await self._get_user(id=user_id, username=username)
        if not user:
            raise InvalidTokenHTTPException()
        return user

    async def _validate_refresh_token(self, refresh_token_from_cookies: uuid.UUID) -> None:
        refresh_token_from_db = await self.__refresh_token_service.get_token(refresh_token=refresh_token_from_cookies)
        if not refresh_token_from_db:
            raise WrongRefreshTokenHTTPException()

        current_time = datetime.now(timezone.utc)
        if current_time >= refresh_token_from_db.expires_at:
            raise RefreshTokenExpiredHTTPException()

    async def _get_user(self, **filter_by) -> User | None:
        user = await self.__user_service.get_user(**filter_by)
        return user

    async def _register_user_in_db(self, data: UserCreateSchema) -> User:
        user = await self.__user_service.create_user({
            "username": data.username,
            "password_hash": self._hash_password(data.password),
        })
        return user

    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8'),
        )

    def _get_jwt_payload(self, user: User) -> dict[str, str]:
        jwt_payload = {
            "sub": str(user.id),
            "username": user.username,
        }
        return jwt_payload

    def _get_refresh_token_creation_data(self, user: User) -> dict[str, Any]:
        refresh_token_creation_data = {
            "user_id": user.id,
            "expires_at": datetime.now() + timedelta(days=30),
        }
        return refresh_token_creation_data


@lru_cache
def get_auth_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    user_service: UserService = Depends(get_user_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    cookies_service: CookiesService = Depends(get_cookies_service),
) -> AuthService:
    return AuthService(jwt_service, user_service, refresh_token_service, cookies_service)
