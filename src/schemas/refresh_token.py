import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RefreshTokenSchema(BaseModel):
    id: int
    user_id: uuid.UUID
    refresh_token: uuid.UUID
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenCreateSchema(BaseModel):
    user_id: uuid.UUID
    expires_at: datetime
