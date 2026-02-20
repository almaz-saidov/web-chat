import re
import uuid
from datetime import datetime

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)


class BaseUserSchema(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseUserSchema):
    pass


class UserSchema(BaseUserSchema):
    password_hash: str


class BaseUserOperationSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers and underscores")
        return v


class UserCreateSchema(BaseUserOperationSchema):
    password: str = Field(..., min_length=6)
    password_confirmation: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match")
        return self


class UserLoginSchema(BaseUserOperationSchema):
    password: str = Field(...)


class UserCreateDatabaseSchema(BaseModel):
    username: str
    password_hash: str
