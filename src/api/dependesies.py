from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from database.unit_of_work import unit_of_work


async def get_uow_session() -> AsyncIterator[AsyncSession]:
    async with unit_of_work() as session:
        yield session
