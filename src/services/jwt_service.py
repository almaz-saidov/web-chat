from datetime import datetime, timedelta, timezone

import jwt

from core.config import settings
from schemas.jwt import JWTPayloadSchema


class JWTService:
    def encode_jwt(self, payload: JWTPayloadSchema) -> str:
        to_encode = payload.model_copy()

        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.exp = int(expire.timestamp())

        return jwt.encode(
            payload=to_encode.model_dump(), key=settings.PRIVATE_KEY_PATH.read_text(), algorithm=settings.ALGORITHM
        )

    def decode_jwt(self, token: str) -> JWTPayloadSchema:
        decoded_jwt = jwt.decode(
            jwt=token,
            key=settings.PUBLIC_KEY_PATH.read_text(),
            algorithms=[settings.ALGORITHM],
            verify_exp=True,
            require=["exp"],
        )

        return JWTPayloadSchema(**decoded_jwt)


def get_jwt_service() -> JWTService:
    return JWTService()
