from fastapi import Depends

from database.repositories.message_repository import MessageRepository
from schemas.message import MessageCreateSchema, MessageSchema
from schemas.user import UserSchema


class MessageService:
    def __init__(self, repository: MessageRepository = Depends()) -> None:
        self._repository = repository

    async def get_all(self) -> list[MessageSchema]:
        return await self._repository.get_all()

    async def create(
        self, message_create_data: MessageCreateSchema, user: UserSchema
    ) -> MessageSchema:
        return await self._repository.create(
            message_create_data=message_create_data, user=user
        )
