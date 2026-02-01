import os
from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env")


class Settings(BaseSettings):
    HOST: str
    PORT: int

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    PRIVATE_KEY_PATH: Path = os.path.join(BASE_DIR, "core", "certs", "jwt-private.pem")
    PUBLIC_KEY_PATH: Path = os.path.join(BASE_DIR, "core", "certs", "jwt-public.pem")
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings: Final = Settings()
