import uuid

from sqlalchemy import delete, insert, select

from database.models.refresh_token import RefreshToken
from database.repositories.base_repository import BaseRepository
from schemas.refresh_token import RefreshTokenCreateSchema, RefreshTokenSchema


class RefreshTokenRepository(BaseRepository):
    async def create(self, refresh_token_create_data: RefreshTokenCreateSchema) -> RefreshTokenSchema:
        query = insert(RefreshToken).values(**refresh_token_create_data.model_dump()).returning(RefreshToken)

        result = await self._session.execute(query)
        refresh_token = result.scalar_one()

        return RefreshTokenSchema.model_validate(refresh_token)

    async def get_by_user_id(self, user_id: uuid.UUID) -> RefreshTokenSchema | None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)

        result = await self._session.execute(query)
        refresh_token = result.scalar_one_or_none()

        return RefreshTokenSchema.model_validate(refresh_token) if refresh_token else None

    async def get_by_token(self, token: uuid.UUID) -> RefreshTokenSchema | None:
        query = select(RefreshToken).where(RefreshToken.refresh_token == token)

        result = await self._session.execute(query)
        refresh_token = result.scalar_one_or_none()

        return RefreshTokenSchema.model_validate(refresh_token) if refresh_token else None

    async def force_delete_by_user_id(self, user_id: uuid.UUID) -> None:
        query = delete(RefreshToken).where(RefreshToken.user_id == user_id)

        await self._session.execute(query)

    async def force_delete_by_token(self, refresh_token: uuid.UUID) -> None:
        query = delete(RefreshToken).where(RefreshToken.refresh_token == refresh_token)

        await self._session.execute(query)
