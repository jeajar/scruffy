from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OVERSEER_URL: HttpUrl
    OVERSEER_API_KEY: str

    SONARR_URL: HttpUrl
    SONARR_API_KEY: str

    RADARR_URL: HttpUrl
    RADARR_API_KEY: str

    RETENTION_DAYS: int = 30
    REMINDER_DAYS: int = 7

    # Email Settings
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: EmailStr
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False


settings = Settings()
