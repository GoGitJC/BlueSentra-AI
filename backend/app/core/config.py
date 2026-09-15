from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bluesentra_env: str = "dev"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg://bluesentra:bluesentra@localhost:5432/bluesentra"
    )

    bluesentra_viewer_msp_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
