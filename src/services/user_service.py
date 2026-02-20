import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repository import UserRepository
from database.session import get_session
from schemas.user import UserCreateDatabaseSchema, UserSchema
from services.db_service import DatabaseService


class UserService(DatabaseService[UserRepository]):
    async def get_by_id(self, user_id: uuid.UUID) -> UserSchema:
        return await self._repository.get_by_id(user_id=user_id)

    async def get_by_username(self, username: str) -> UserSchema:
        return await self._repository.get_by_username(username=username)

    async def create(self, user_create_data: UserCreateDatabaseSchema) -> UserSchema:
        return await self._repository.create(user_create_data=user_create_data)

    def _create_repository(self) -> UserRepository:
        return UserRepository(session=self._session)


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session=session)
