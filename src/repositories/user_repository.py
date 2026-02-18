from database.models import User
from database.repositories import InsertOneRepository, SelectOneRepository


class UserRepository(
    InsertOneRepository[User],
    SelectOneRepository[User],
):
    _cls_model = User

    async def get_user(self, **filter_by) -> User | None:
        return await self.select_one(**filter_by)

    async def create_user(self, data: dict[str, str]) -> User:
        return await self.insert_one(data)
