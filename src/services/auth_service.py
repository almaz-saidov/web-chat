import uuid
from functools import lru_cache
from typing import Any, Optional

import bcrypt
from fastapi import Depends
from jwt.exceptions import InvalidTokenError

from api.schemas import TokenInfo, UserCreate, UserLogin
from core.exceptions import (InvalidTokenHTTPException,
                             UserAlreadyExistsHTTPException,
                             WrongUsernameOrPasswordHTTPException)
from database.models import User
from services.jwt_service import JWTService, get_jwt_service
from services.user_service import UserService, get_user_service


class AuthService:
    def __init__(self, jwt_service: JWTService, user_service: UserService) -> None:
        self.jwt_service = jwt_service
        self.user_service = user_service

    async def register_user(self, user_data: UserCreate) -> User:
        user = await self._get_user(username=user_data.username)
        if user:
            raise UserAlreadyExistsHTTPException()

        return await self._register_user_in_db(user_data)

    async def authenticate_user(
        self,
        sign_in_data: UserLogin,
    ) -> TokenInfo:
        user = await self._get_user(username=sign_in_data.username)            
        if not user or not self._verify_password(sign_in_data.password, user.password_hash):
            raise WrongUsernameOrPasswordHTTPException()

        jwt_payload = self._get_jwt_payload(user)
        access_token = self.jwt_service.encode_jwt(jwt_payload)

        return TokenInfo(access_token=access_token)

    async def authorize_user(
        self,
        token: str,
    ) -> User:
        try:
            payload = self.jwt_service.decode_jwt(token)
        except InvalidTokenError:
            raise InvalidTokenHTTPException()

        user = await self._get_user_via_payload(payload)
        return user

    async def _get_user_via_payload(self, payload: dict[str, Any]) -> User:
        user_id = uuid.UUID(payload.get("sub"))
        username: str = payload.get("username")

        user = await self._get_user(id=user_id, username=username)
        if not user:
            raise InvalidTokenHTTPException()
        return user

    async def _get_user(self, **filter_by) -> Optional[User]:
        user = await self.user_service.get_user(**filter_by)
        return user

    async def _register_user_in_db(self, data: UserCreate) -> User:
        user = await self.user_service.create_user({
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


@lru_cache
def get_auth_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(jwt_service, user_service)
