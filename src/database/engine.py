from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.config import settings

engine = create_async_engine(settings.DB_URL)

async_db_session_factory = async_sessionmaker(engine, expire_on_commit=False)
