import uuid

from sqlalchemy import insert, select

from database.models.user import User
from database.repositories.base_repository import BaseRepository
from schemas.user import UserCreateDatabaseSchema, UserSchema


class UserRepository(BaseRepository):
    async def create(self, user_create_data: UserCreateDatabaseSchema) -> UserSchema:
        query = insert(User).values(**user_create_data.model_dump()).returning(User)

        result = await self._session.execute(query)
        user = result.scalar_one()

        return UserSchema.model_validate(user)

    async def get_by_id(self, user_id: uuid.UUID) -> UserSchema | None:
        query = select(User).where(User.id == user_id)

        result = await self._session.execute(query)
        user = result.scalar_one_or_none()

        return UserSchema.model_validate(user) if user else None

    async def get_by_username(self, username: str) -> UserSchema | None:
        query = select(User).where(User.username == username)

        result = await self._session.execute(query)
        user = result.scalar_one_or_none()

        return UserSchema.model_validate(user) if user else None
