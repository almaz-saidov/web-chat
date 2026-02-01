from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from core.config import settings


class JWTService:
    def encode_jwt(
        self,
        payload: dict[str, Any],
        private_key: str = settings.PRIVATE_KEY_PATH.read_text(),
        algorithm: str = settings.ALGORITHM,
        expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> str:
        to_encode = payload.copy()

        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        to_encode.update(exp=expire)

        return jwt.encode(to_encode, private_key, algorithm)

    def decode_jwt(
        self,
        token: str,
        public_key: str = settings.PUBLIC_KEY_PATH.read_text(),
        algorithm: str = settings.ALGORITHM,
    ) -> str:
        return jwt.decode(token, public_key, algorithms=[algorithm])


def get_jwt_service() -> JWTService:
    return JWTService()
