from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OVERSEERR_URL: HttpUrl
    OVERSEERR_API_KEY: str

    SONARR_URL: HttpUrl
    SONARR_API_KEY: str

    RADARR_URL: HttpUrl
    RADARR_API_KEY: str

    RETENTION_DAYS: int = 30
    REMINDER_DAYS: int = 7

    # Email Settings
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: EmailStr = "scruffy@example.com"
    SMTP_SSL_TLS: bool = True
    SMTP_STARTTLS: bool = False

    # Application settings
    LOG_LEVEL: str = "INFO"


settings = Settings()
