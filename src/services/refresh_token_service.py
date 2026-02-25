import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import InvalidRefreshTokenFormatHTTPException, InvalidTokenHTTPException
from database.repositories.refresh_token_repository import RefreshTokenRepository
from database.session import get_session
from schemas.refresh_token import RefreshTokenCreateSchema, RefreshTokenSchema
from services.db_service import DatabaseService


class RefreshTokenService(DatabaseService[RefreshTokenRepository]):
    async def create_token(self, refresh_token_create_data: RefreshTokenCreateSchema) -> RefreshTokenSchema:
        await self._force_delete_existing_tokens(refresh_token_create_data=refresh_token_create_data)

        return await self._repository.create(refresh_token_create_data=refresh_token_create_data)

    async def get_by_token(self, token: uuid.UUID) -> RefreshTokenSchema:
        refresh_token = await self._repository.get_by_token(token=token)

        if not refresh_token:
            raise InvalidTokenHTTPException()
        return refresh_token

    async def delete_by_token(self, token: uuid.UUID) -> None:
        await self._repository.force_delete_by_token(token=token)

    def validate_refresh_token_str(self, refresh_token_str: str) -> uuid.UUID:
        try:
            return uuid.UUID(refresh_token_str)
        except ValueError:
            raise InvalidRefreshTokenFormatHTTPException()

    async def _force_delete_existing_tokens(self, refresh_token_create_data: RefreshTokenCreateSchema) -> None:
        if await self._repository.get_by_user_id(user_id=refresh_token_create_data.user_id):
            await self._repository.force_delete_by_user_id(user_id=refresh_token_create_data.user_id)

    def _create_repository(self) -> RefreshTokenRepository:
        return RefreshTokenRepository(session=self._session)


def get_refresh_token_service(session: AsyncSession = Depends(get_session)) -> RefreshTokenService:
    return RefreshTokenService(session=session)
