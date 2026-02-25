from datetime import datetime, timedelta, timezone

import jwt

from core.config import settings
from schemas.jwt import JWTPayloadSchema


class JWTService:
    def encode_jwt(
        self,
        payload: JWTPayloadSchema,
        private_key: str = settings.PRIVATE_KEY_PATH.read_text(),
        algorithm: str = settings.ALGORITHM,
        expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> str:
        to_encode = payload.model_copy()

        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        to_encode.exp = int(expire.timestamp())

        return jwt.encode(payload=to_encode.model_dump(), key=private_key, algorithm=algorithm)

    def decode_jwt(
        self,
        token: str,
        public_key: str = settings.PUBLIC_KEY_PATH.read_text(),
        algorithm: str = settings.ALGORITHM,
    ) -> JWTPayloadSchema:
        decoded_jwt = jwt.decode(
            jwt=token,
            key=public_key,
            algorithms=[algorithm],
            verify_exp=True,
            require=["exp"],
        )

        return JWTPayloadSchema(**decoded_jwt)


def get_jwt_service() -> JWTService:
    return JWTService()
