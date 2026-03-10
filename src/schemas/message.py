import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageSchema(BaseModel):
    id: uuid.UUID
    username: str
    content: str
    created_at: datetime


class MessageCreateSchema(BaseModel):
    content: str


class MessageCreateDatabaseSchema(BaseModel):
    user_id: uuid.UUID
    content: str
