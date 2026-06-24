import os
from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "core", "envs", ".env")


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

    SIGNATURE_SAMPLE_COUNT: int = Field(default=5, gt=0)
    SIGNATURE_MIN_POINT_COUNT: int = Field(default=5, gt=0)
    SIGNATURE_NORMALIZED_POINT_COUNT: int = Field(default=1024, gt=1)
    SIGNATURE_MATCH_THRESHOLD: float = Field(default=0.85, ge=0, le=1)
    SIGNATURE_COORDINATE_WEIGHT: float = Field(default=1.0, ge=0)
    SIGNATURE_PRESSURE_WEIGHT: float = Field(default=0.35, ge=0)
    SIGNATURE_TILT_WEIGHT: float = Field(default=0.35, ge=0)
    SIGNATURE_TIME_WEIGHT: float = Field(default=0.15, ge=0)
    SIGNATURE_DURATION_WEIGHT: float = Field(default=0.4, ge=0)
    SIGNATURE_BREAK_COUNT_WEIGHT: float = Field(default=0.3, ge=0)
    SIGNATURE_MAX_DURATION_PENALTY_RATIO: float = Field(default=2.0, ge=0)

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings: Final = Settings()
