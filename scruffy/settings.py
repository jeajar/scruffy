from typing import Optional

from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    overseerr_url: HttpUrl = "http://localhost:5050"
    overseerr_api_key: Optional[str] = None

    sonarr_url: HttpUrl = "http://localhost:8989"
    sonarr_api_key: Optional[str] = None

    radarr_url: HttpUrl = "http://localhost:7878"
    radarr_api_key: Optional[str] = None

    retention_days: int = 30
    reminder_days: int = 7

    # Email Settings
    email_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: EmailStr = "scruffy@example.com"
    smtp_ssl_tls: bool = True
    smtp_starttls: bool = False

    # Application settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    data_dir: Optional[str] = ""


settings = Settings()
