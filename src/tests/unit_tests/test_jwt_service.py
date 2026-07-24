import uuid

import pytest
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from core.config import settings
from schemas.jwt import JWTPayloadSchema
from services.jwt_service import JWTService


def test_decode_jwt_returns_payload_for_encoded_token(jwt_keys: None) -> None:
    service = JWTService()
    payload = JWTPayloadSchema(sub=str(uuid.uuid4()), username="almaz")

    token = service.encode_jwt(payload=payload)
    decoded_payload = service.decode_jwt(token=token)

    assert decoded_payload.sub == payload.sub, (
        "Decoded JWT subject must match encoded payload subject"
    )
    assert decoded_payload.username == payload.username, (
        "Decoded JWT username must match encoded payload username"
    )
    assert decoded_payload.exp is not None, (
        "Decoded JWT payload must contain expiration timestamp"
    )


def test_decode_jwt_raises_error_for_invalid_token(jwt_keys: None) -> None:
    service = JWTService()

    with pytest.raises(InvalidTokenError):
        service.decode_jwt(token="invalid-token")


def test_decode_jwt_raises_error_for_expired_token(jwt_keys: None) -> None:
    service = JWTService()
    original_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = -1

    try:
        token = service.encode_jwt(
            payload=JWTPayloadSchema(sub=str(uuid.uuid4()), username="almaz")
        )
    finally:
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = original_expire_minutes

    with pytest.raises(ExpiredSignatureError):
        service.decode_jwt(token=token)
