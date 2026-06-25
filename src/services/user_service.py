import uuid

from fastapi import Depends

from core.exceptions import UserNotFoundHTTPException
from database.repositories.user_repository import UserRepository
from schemas.user import UserCreateDatabaseSchema, UserSchema
from services.db_service import DatabaseService


class UserService(DatabaseService[UserRepository]):
    async def get_by_id(self, user_id: uuid.UUID) -> UserSchema:
        user = await self._repository.get_by_id(user_id=user_id)

        if not user:
            raise UserNotFoundHTTPException()
        return user

    async def get_by_username(self, username: str) -> UserSchema | None:
        return await self._repository.get_by_username(username=username)

    async def create(self, user_create_data: UserCreateDatabaseSchema) -> UserSchema:
        return await self._repository.create(user_create_data=user_create_data)


def get_user_service(repository: UserRepository = Depends()) -> UserService:
    return UserService(repository=repository)
