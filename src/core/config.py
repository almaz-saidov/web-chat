import os
from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env")


class Settings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 8000

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "db_user"
    DB_PASS: str = "db_pass"
    DB_NAME: str = "db_name"

    PRIVATE_KEY_PATH: Path = Path(os.path.join(BASE_DIR, "core", "certs", "jwt-private.pem"))
    PUBLIC_KEY_PATH: Path = Path(os.path.join(BASE_DIR, "core", "certs", "jwt-public.pem"))
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings: Final = Settings()
