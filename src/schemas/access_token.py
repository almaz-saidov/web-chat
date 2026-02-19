from pydantic import BaseModel, Field


class AccessTokenSchema(BaseModel):
    access_token: str = Field(description="JWT токен доступа")
    token_type: str = Field(default="Bearer", description="Тип токена")
