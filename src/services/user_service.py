from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserCreateSchema
from database.models import User
from database.unit_of_work import get_uow_session
from repositories.user_repository import UserRepository
from services.db_service import DbService


class UserService(DbService[UserRepository]):
    async def get_user(self, **filter_by) -> User | None:
        return await self._repository.get_user(**filter_by)

    async def create_user(self, user_create_data: UserCreateSchema) -> User:
        return await self._repository.create_user(data=user_create_data.model_dump())

    def _create_repository(self) -> UserRepository:
        return UserRepository(session=self._session)


def get_user_service(session: AsyncSession = Depends(get_uow_session)) -> UserService:
    return UserService(session=session)
