from database.models import Message
from database.repositories import InsertOneRepository, SelectAllRepository


class MessageRepository(
    InsertOneRepository[Message],
    SelectAllRepository[Message],
):
    cls_model = Message

    async def create_message(self, data: dict[str, str]) -> Message:
        return await self.insert_one(data)

    async def get_all_messages(self) -> list[Message]:
        return await self.select_all()
