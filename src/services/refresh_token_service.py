from functools import lru_cache
from typing import Any, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RefreshToken
from database.unit_of_work import get_uow_session
from repositories.refresh_token_repository import RefreshTokenRepository
from services.db_service import DbService


class RefreshTokenService(DbService[RefreshTokenRepository]):
    async def create_token(self, data: dict[str, Any]) -> RefreshToken:
        await self._force_delete_existing_tokens(data)

        return await self._repository.create_token(data)

    async def get_token(self, **filter_by) -> Optional[RefreshToken]:
        return await self._repository.get_token(**filter_by)

    async def _force_delete_existing_tokens(self, data: dict[str, Any]) -> None:
        user_id = data.get("user_id")
        if await self.get_token(user_id=user_id):
            await self._repository.force_delete_tokens(user_id=user_id)

    def _create_repository(self) -> RefreshTokenRepository:
        return RefreshTokenRepository(self._session)


@lru_cache
def get_refresh_token_service(session: AsyncSession = Depends(get_uow_session)) -> RefreshTokenService:
    return RefreshTokenService(session)
