from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.message_repository import MessageRepository
from database.session import get_session
from schemas.message import MessageCreateSchema, MessageSchema
from schemas.user import UserSchema
from services.db_service import DatabaseService


class MessageService(DatabaseService[MessageRepository]):
    async def get_all(self) -> list[MessageSchema]:
        return await self._repository.get_all()

    async def create(self, message_create_data: MessageCreateSchema, user: UserSchema) -> MessageSchema:
        return await self._repository.create(message_create_data=message_create_data, user=user)

    def _create_repository(self) -> MessageRepository:
        return MessageRepository(session=self._session)


def get_message_service(session: AsyncSession = Depends(get_session)) -> MessageService:
    return MessageService(session=session)
