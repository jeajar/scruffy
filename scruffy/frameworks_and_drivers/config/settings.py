from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    overseerr_url: HttpUrl = "http://localhost:5050"
    overseerr_api_key: str | None = None

    sonarr_url: HttpUrl = "http://localhost:8989"
    sonarr_api_key: str | None = None

    radarr_url: HttpUrl = "http://localhost:7878"
    radarr_api_key: str | None = None

    retention_days: int = 30
    reminder_days: int = 7
    extension_days: int = 7

    # Application URL for email links (e.g. https://scruffy.example.com)
    app_base_url: str = "http://localhost:5173"

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

    # Loki Settings (optional)
    loki_enabled: bool = False
    loki_url: HttpUrl | None = None  # e.g., "http://loki:3100/loki/api/v1/push"
    loki_labels: dict[str, str] = {"app": "scruffy"}

    # API Server settings
    api_enabled: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_workers: int = 1  # Note: workers > 1 runs scheduler per worker (duplicate jobs)
    api_secret_key: str = "change-me-in-production"  # For session signing

    # CORS settings for frontend
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
