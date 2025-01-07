from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OVERSEER_URL: HttpUrl
    OVERSEER_API_KEY: str

    SONARR_URL: HttpUrl
    SONARR_API_KEY: str

    RADARR_URL: HttpUrl
    RADARR_API_KEY: str

    RETENTION_DAYS: int = 30
    REMINDER_DAYS: int = 26


settings = Settings()
