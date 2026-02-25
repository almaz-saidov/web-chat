import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
from fastapi import Depends, Request, Response
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from core.exceptions import (
    AccessTokenExpiredHTTPException,
    InvalidTokenHTTPException,
    RefreshTokenExpiredHTTPException,
    TokenIsInvalidOrExpiredWebSocketException,
    UserAlreadyExistsHTTPException,
    WrongRefreshTokenHTTPException,
    WrongUsernameOrPasswordHTTPException,
)
from schemas.access_token import AccessTokenSchema
from schemas.jwt import JWTPayloadSchema
from schemas.refresh_token import RefreshTokenCreateSchema, RefreshTokenSchema
from schemas.user import UserCreateDatabaseSchema, UserCreateSchema, UserLoginSchema, UserResponseSchema, UserSchema
from services.cookies_service import CookiesService, get_cookies_service
from services.jwt_service import JWTService, get_jwt_service
from services.refresh_token_service import RefreshTokenService, get_refresh_token_service
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

    async def register_user(self, user_create_data: UserCreateSchema) -> UserResponseSchema:
        user = await self.__user_service.get_by_username(username=user_create_data.username)
        if user:
            raise UserAlreadyExistsHTTPException()

        user = await self.__user_service.create(
            user_create_data=UserCreateDatabaseSchema(
                username=user_create_data.username,
                password_hash=self._hash_password(user_create_data.password),
            ),
        )
        return UserResponseSchema(**user.model_dump())

    async def authenticate_user(self, login_data: UserLoginSchema, response: Response) -> AccessTokenSchema:
        user = await self.__user_service.get_by_username(username=login_data.username)
        if not user or not self._verify_password(password=login_data.password, hashed_password=user.password_hash):
            raise WrongUsernameOrPasswordHTTPException()

        access_token = await self._create_tokens(user=user, response=response)

        return AccessTokenSchema(access_token=access_token)

    async def authorize_user(self, token: str) -> UserSchema:
        try:
            payload = self.__jwt_service.decode_jwt(token=token)
            user = await self._get_user_via_payload(payload=payload)
            return user
        except ExpiredSignatureError:
            raise AccessTokenExpiredHTTPException()
        except InvalidTokenError:
            raise InvalidTokenHTTPException()

    async def logout_user(self, request: Request, response: Response) -> None:
        refresh_token_from_cookies_str = self.__cookies_service.get_refresh_token_from_cookies(request=request)
        refresh_token_from_cookies = self.__refresh_token_service.validate_refresh_token_str(
            refresh_token_str=refresh_token_from_cookies_str
        )

        await self.__refresh_token_service.delete_by_token(token=refresh_token_from_cookies)
        self.__cookies_service.delete_cookies(response=response)

    async def authorize_websocket_user(self, token: str) -> UserSchema:
        try:
            payload = self.__jwt_service.decode_jwt(token=token)
            user = await self._get_user_via_payload(payload=payload)
            return user
        except (ExpiredSignatureError, InvalidTokenError):
            raise TokenIsInvalidOrExpiredWebSocketException()

    async def refresh_tokens(self, request: Request, response: Response) -> AccessTokenSchema:
        refresh_token_from_cookies_str = self.__cookies_service.get_refresh_token_from_cookies(request=request)
        refresh_token_from_cookies = self.__refresh_token_service.validate_refresh_token_str(
            refresh_token_str=refresh_token_from_cookies_str
        )

        refresh_token_from_db = await self._validate_refresh_token(
            refresh_token_from_cookies=refresh_token_from_cookies
        )

        user = await self.__user_service.get_by_id(user_id=refresh_token_from_db.user_id)
        access_token = await self._create_tokens(user=user, response=response)

        return AccessTokenSchema(access_token=access_token)

    async def _create_tokens(self, user: UserSchema, response: Response) -> str:
        jwt_payload = JWTPayloadSchema(sub=str(user.id), username=user.username)
        access_token = self.__jwt_service.encode_jwt(payload=jwt_payload)

        refresh_token_create_data = self._get_refresh_token_creation_data(user=user)
        refresh_token = await self.__refresh_token_service.create_token(
            refresh_token_create_data=refresh_token_create_data
        )
        self.__cookies_service.set_cookies(response=response, refresh_token=refresh_token)

        return access_token

    async def _get_user_via_payload(self, payload: JWTPayloadSchema) -> UserSchema:
        return await self.__user_service.get_by_id(user_id=uuid.UUID(payload.sub))

    async def _validate_refresh_token(self, refresh_token_from_cookies: uuid.UUID) -> RefreshTokenSchema:
        refresh_token_from_db = await self.__refresh_token_service.get_by_token(token=refresh_token_from_cookies)
        if not refresh_token_from_db:
            raise WrongRefreshTokenHTTPException()

        current_time = datetime.now(timezone.utc)
        if current_time >= refresh_token_from_db.expires_at:
            raise RefreshTokenExpiredHTTPException()

        return refresh_token_from_db

    def _hash_password(self, password: str) -> str:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_password.decode("utf-8")

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    def _get_refresh_token_creation_data(self, user: UserSchema) -> RefreshTokenCreateSchema:
        refresh_token_creation_data = RefreshTokenCreateSchema(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        return refresh_token_creation_data


@lru_cache
def get_auth_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    user_service: UserService = Depends(get_user_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    cookies_service: CookiesService = Depends(get_cookies_service),
) -> AuthService:
    return AuthService(
        jwt_service=jwt_service,
        user_service=user_service,
        refresh_token_service=refresh_token_service,
        cookies_service=cookies_service,
    )
