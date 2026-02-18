from typing import Any

from database.models import RefreshToken
from database.repositories import (ForceDeleteRepository, InsertOneRepository,
                                   SelectOneRepository)


class RefreshTokenRepository(
    ForceDeleteRepository[RefreshToken],
    InsertOneRepository[RefreshToken],
    SelectOneRepository[RefreshToken],
):
    _cls_model = RefreshToken

    async def force_delete_tokens(self, **filter_by) -> None:
        await self.force_delete(**filter_by)

    async def create_token(self, data: dict[str, Any]) -> RefreshToken:
        return await self.insert_one(data)

    async def get_token(self, **filter_by) -> RefreshToken | None:
        return await self.select_one(**filter_by)
