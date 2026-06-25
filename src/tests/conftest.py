from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from core.config import settings
from database.session import get_db_session

TEST_POSTGRES_IMAGE = "postgres:16-alpine"


def run_migrations() -> None:
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def test_db_url() -> Iterator[str]:
    with PostgresContainer(TEST_POSTGRES_IMAGE, driver="asyncpg") as postgres:
        test_database_url = postgres.get_connection_url(driver="asyncpg")
        settings.TEST_DB_URL = test_database_url
        run_migrations()

        yield test_database_url

        settings.TEST_DB_URL = None


@pytest_asyncio.fixture
async def test_db_engine(test_db_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(test_db_url, echo=False, future=True)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def jwt_keys(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    keys_dir = tmp_path_factory.mktemp("jwt")
    private_key_path = keys_dir / "jwt-private.pem"
    public_key_path = keys_dir / "jwt-public.pem"

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    original_private_key_path = settings.PRIVATE_KEY_PATH
    original_public_key_path = settings.PUBLIC_KEY_PATH
    settings.PRIVATE_KEY_PATH = private_key_path
    settings.PUBLIC_KEY_PATH = public_key_path

    yield

    settings.PRIVATE_KEY_PATH = original_private_key_path
    settings.PUBLIC_KEY_PATH = original_public_key_path


@pytest.fixture
def test_app() -> FastAPI:
    from main import app

    return app


@pytest_asyncio.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(
    test_app: FastAPI,
    test_db_engine: AsyncEngine,
    jwt_keys: None,
) -> AsyncIterator[AsyncClient]:
    async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as error:
                await session.rollback()
                raise error
            finally:
                await session.close()

    original_overrides = dict(test_app.dependency_overrides)
    test_app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    test_app.dependency_overrides.clear()
    test_app.dependency_overrides.update(original_overrides)
