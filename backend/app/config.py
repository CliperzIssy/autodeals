from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://autodeals:autodeals_dev@localhost:5432/autodeals"
    database_url_sync: str = "postgresql://autodeals:autodeals_dev@localhost:5432/autodeals"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # IPRoyal Proxy
    iproyal_username: str = ""
    iproyal_password: str = ""
    iproyal_host: str = "geo.iproyal.com"
    iproyal_port: int = 12321

    # Gemini AI
    gemini_api_key: str = ""

    # App
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # BPM
    bpm_rates_version: str = "2025"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
