import functools
from typing import AsyncGenerator

from sqlalchemy import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from core.config import settings


@functools.lru_cache
def get_engine(url: str | URL) -> AsyncEngine:
    return create_async_engine(url, echo=False, future=True)


def get_async_session(url: str | URL) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(url), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = get_async_session(url=settings.DB_URL)

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
