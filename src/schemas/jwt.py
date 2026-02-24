from pydantic import BaseModel


class JWTPayloadSchema(BaseModel):
    sub: str
    username: str
    exp: int | None = None
