from pydantic import BaseModel, Field


class AccessTokenSchema(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(default="Bearer")
