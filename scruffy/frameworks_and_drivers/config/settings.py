from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    overseerr_url: HttpUrl = "http://localhost:5050"
    overseerr_api_key: str | None = None

    sonarr_url: HttpUrl = "http://localhost:8989"
    sonarr_api_key: str | None = None

    radarr_url: HttpUrl = "http://localhost:7878"
    radarr_api_key: str | None = None

    retention_days: int = 30
    reminder_days: int = 7

    # Email Settings
    email_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: EmailStr = "scruffy@example.com"
    smtp_ssl_tls: bool = True
    smtp_starttls: bool = False

    # Application settings
    log_level: str = "INFO"
    log_file: str | None = None
    data_dir: str | None = ""


settings = Settings()
