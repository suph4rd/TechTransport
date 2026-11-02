from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://tech_transport:local-development-only@localhost:5432/tech_transport"
    photos_dir: Path = Path("/data/photos")
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
