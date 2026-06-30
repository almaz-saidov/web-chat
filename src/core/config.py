import os
from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env")
MAX_PORT_NUMBER: Final = 65535


class Settings(BaseSettings):
    SERVER_HOST: str = Field(default="0.0.0.0")
    SERVER_PORT: int = Field(default=8000, gt=0, le=MAX_PORT_NUMBER)

    POSTGRES_HOST: str = Field(default="web-chat-db")
    POSTGRES_PORT: int = Field(default=5432, gt=0, le=MAX_PORT_NUMBER)
    POSTGRES_USER: str = Field(default="db_user")
    POSTGRES_PASSWORD: str = Field(default="db_pass")
    POSTGRES_DB: str = Field(default="db_name")

    PRIVATE_KEY_PATH: Path = Field(default=Path(os.path.join(BASE_DIR, "core", "certs", "jwt-private.pem")))
    PUBLIC_KEY_PATH: Path = Field(default=Path(os.path.join(BASE_DIR, "core", "certs", "jwt-public.pem")))
    ALGORITHM: str = Field(default="RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, gt=0)

    TEST_DB_URL: str | None = Field(default=None)

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings: Final = Settings()
