import os
from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env.dev")


class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    POSTGRES_HOST: str = "web-chat-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "db_user"
    POSTGRES_PASSWORD: str = "db_pass"
    POSTGRES_DB: str = "db_name"

    PRIVATE_KEY_PATH: Path = Path(os.path.join(BASE_DIR, "core", "certs", "jwt-private.pem"))
    PUBLIC_KEY_PATH: Path = Path(os.path.join(BASE_DIR, "core", "certs", "jwt-public.pem"))
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings: Final = Settings()
