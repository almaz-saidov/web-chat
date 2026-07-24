from sqlalchemy import insert, literal, select

from database.models import Message, User
from database.repositories.base_repository import BaseDatabaseRepository
from schemas.message import (
    MessageCreateDatabaseSchema,
    MessageCreateSchema,
    MessageSchema,
)
from schemas.user import UserSchema


class MessageRepository(BaseDatabaseRepository):
    async def create(
        self, message_create_data: MessageCreateSchema, user: UserSchema
    ) -> MessageSchema:
        message_db_create_data = MessageCreateDatabaseSchema(
            user_id=user.id, content=message_create_data.content
        )
        query = (
            insert(Message)
            .values(**message_db_create_data.model_dump())
            .returning(
                Message.id,
                literal(user.username).label("username"),
                Message.content,
                Message.created_at,
            )
        )

        result = await self._session.execute(query)
        message_data = result.mappings().one()

        return MessageSchema.model_validate(message_data)

    async def get_all(self) -> list[MessageSchema]:
        query = (
            select(
                Message.id,
                User.username.label("username"),
                Message.content,
                Message.created_at,
            )
            .join(User, User.id == Message.user_id)
            .order_by(Message.created_at)
        )

        result = await self._session.execute(query)
        messages_data = result.mappings().all()

        return [
            MessageSchema.model_validate(message_data) for message_data in messages_data
        ]
