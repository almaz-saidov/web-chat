from sqlalchemy import insert, select

from database.models import Message, User
from database.repositories.base_repository import BaseRepository
from schemas.message import MessageCreateDatabaseSchema, MessageSchema


class MessageRepository(BaseRepository):
    async def create(self, message_create_data: MessageCreateDatabaseSchema) -> MessageSchema:
        query = insert(Message).values(**message_create_data.model_dump()).returning(Message)

        result = await self._session.execute(query)
        message = result.scalar_one()

        user_query = select(User).where(User.id == message.user_id)
        user_result = await self._session.execute(user_query)
        user = user_result.scalar_one()

        return MessageSchema(
            id=message.id,
            username=user.username,
            content=message.content,
            created_at=message.created_at,
        )

    async def get_all(self) -> list[MessageSchema]:
        query = select(Message, User).join(User, User.id == Message.user_id).order_by(Message.created_at)

        result = await self._session.execute(query)
        rows = result.all()

        return [
            MessageSchema(
                id=message.id,
                username=user.username,
                content=message.content,
                created_at=message.created_at,
            )
            for message, user in rows
        ]
