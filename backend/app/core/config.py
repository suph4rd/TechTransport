from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://tech_transport:local-development-only@localhost:5432/tech_transport"
    photos_dir: Path = Path("/data/photos")
    cookie_secure: bool = False
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
