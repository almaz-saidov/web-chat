import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserCreate
from database.models import User
from services.user_service import get_user_service


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_data: UserCreate) -> User:
        user_service = get_user_service(self.session)
        user = await user_service.get_user(username=user_data.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user with this username already exists",
            )

        return await user_service.create_user({
            "username": user_data.username,
            "password_hash": self._hash_password(user_data.password),
        })

    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8'),
        )


def get_auth_service(session: AsyncSession) -> AuthService:
    return AuthService(session)
