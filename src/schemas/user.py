import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, description="Пароль")
    password_confirmation: str = Field(..., min_length=6, description="Подтверждение пароля")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers and underscores")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match")
        return self


class UserLoginSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., description="Пароль пользователя")


class UserResponseSchema(BaseModel):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор пользователя в формате UUID")
    username: str = Field(..., description="Имя пользователя")
    created_at: datetime = Field(..., description="Дата и время регистрации пользователя")

    class Config:
        from_attributes = True