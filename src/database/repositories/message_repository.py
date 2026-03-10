from sqlalchemy import insert, select

from database.models import Message, User
from database.repositories.base_repository import BaseRepository
from schemas.message import MessageCreateDatabaseSchema, MessageCreateSchema, MessageSchema
from schemas.user import UserSchema


class MessageRepository(BaseRepository):
    async def create(self, message_create_data: MessageCreateSchema, user: UserSchema) -> MessageSchema:
        message_db_create_data = MessageCreateDatabaseSchema(user_id=user.id, content=message_create_data.content)
        query = insert(Message).values(**message_db_create_data.model_dump()).returning(Message)

        result = await self._session.execute(query)
        message = result.scalar_one()

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
