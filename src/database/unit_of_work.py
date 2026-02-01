from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from .engine import async_db_session_factory


@asynccontextmanager
async def unit_of_work() -> AsyncIterator[AsyncSession]:
    session = async_db_session_factory()
    try:
        async with session.begin():
            yield session
    finally:
        await session.close()
