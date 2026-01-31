from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserCreate
from database.models import User
from services.user_service import get_user_service
from services.utils import hash_password


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(
        self,
        user_data: UserCreate,
    ) -> User:
        user_service = get_user_service(self.session)
        already_existing_user = await user_service.get_user(username=user_data.username)
        if already_existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user with this username already exists",
            )

        return await user_service.create_user({
            "username": user_data.username,
            "password_hash": hash_password(user_data.password),
        })


def get_auth_service(session: AsyncSession) -> AuthService:
    return AuthService(session)
