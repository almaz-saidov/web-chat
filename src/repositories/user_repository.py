import uuid
from typing import Optional

from database.models import User
from database.repositories import InsertOneRepository, SelectOneRepository


class UserRepository(
    InsertOneRepository[User],
    SelectOneRepository[User],
):
    cls_model = User

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.select_one(username=username)

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.select_one(id=user_id)

    async def create_user(self, data: dict[str, str]) -> User:
        return await self.insert_one(data)
