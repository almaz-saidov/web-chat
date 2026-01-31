from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserCreate
from database.models import User
from repositories.user_repository import UserRepository
from services.db_service import DbService
from services.utils import hash_password


class UserService(DbService[UserRepository]):
    async def register_user(
        self,
        user_data: UserCreate,
    ) -> User:
        already_existing_user = await self.repository.get_user(username=user_data.username)
        if already_existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user with this username already exists",
            )

        password_hash = hash_password(user_data.password)
        return await self.create_user({
            "username": user_data.username,
            "password_hash": password_hash,
        })

    async def create_user(
        self,
        user_data: dict[str, str],
    ) -> User:
        return await self.repository.create_user(user_data)

    def _create_repository(self) -> UserRepository:
        return UserRepository(self.session)


def get_user_service(session: AsyncSession) -> UserService:
    return UserService(session)
