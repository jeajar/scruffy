from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
from pydantic import SecretStr

from scruffy.domain.value_objects import SCRUFFY_QUOTES
from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.interface_adapters.interfaces.settings_provider_interface import (
    ISettingsProvider,
)


class EmailClient:
    """FastMail wrapper for sending emails."""

    def __init__(self, settings_provider: "ISettingsProvider | None" = None):
        """Initialize email client. Uses settings_provider for DB-backed config, else env."""
        self._settings_provider = settings_provider
        templates_path = Path(__file__).parent.parent.parent / "templates"
        self.template_env = Environment(loader=FileSystemLoader(templates_path))

    def _get_config(self) -> dict:
        """Get email config from provider (DB + env) or fallback to env."""
        if self._settings_provider is not None:
            return dict(self._settings_provider.get_email_config())
        return {
            "enabled": settings.email_enabled,
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_username": settings.smtp_username,
            "smtp_password": settings.smtp_password,
            "smtp_from_email": str(settings.smtp_from_email),
            "smtp_ssl_tls": settings.smtp_ssl_tls,
            "smtp_starttls": settings.smtp_starttls,
        }

    def _get_fastmail(self) -> FastMail | None:
        """Build FastMail from current config. Returns None if email disabled."""
        config = self._get_config()
        if not config.get("enabled", False):
            return None
        username = config.get("smtp_username") or ""
        password = config.get("smtp_password") or ""
        use_credentials = bool(username and password)
        conf = ConnectionConfig(
            MAIL_USERNAME=username,
            MAIL_PASSWORD=SecretStr(password),
            MAIL_FROM_NAME="Scruffy, the Janitor",
            MAIL_FROM=config.get("smtp_from_email", "scruffy@example.com"),
            MAIL_PORT=config.get("smtp_port", 25),
            MAIL_SERVER=config.get("smtp_host", "localhost"),
            MAIL_SSL_TLS=config.get("smtp_ssl_tls", True),
            MAIL_STARTTLS=config.get("smtp_starttls", False),
            USE_CREDENTIALS=use_credentials,
        )
        return FastMail(conf)

    async def send_deletion_notice(
        self, to_email: str, title: str, poster: str, days_left: int = 0
    ) -> None:
        """Send deletion notice email."""
        fastmail = self._get_fastmail()
        if not fastmail:
            return

        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media={"title": title, "poster": poster},
            days_left=days_left,
            quote=SCRUFFY_QUOTES.random(),
            reminder=False,
        )

        message = MessageSchema(
            subject=f"Gone!: {title}",
            recipients=[to_email],
            body=html,
            subtype=MessageType.html,
        )

        await fastmail.send_message(message)

    async def send_reminder_notice(
        self,
        to_email: str,
        title: str,
        poster: str,
        days_left: int,
        request_id: int,
    ) -> None:
        """Send reminder notice email."""
        fastmail = self._get_fastmail()
        if not fastmail:
            return

        base_url = (
            self._settings_provider.get_app_base_url()
            if self._settings_provider
            else settings.app_base_url
        ).rstrip("/")
        extend_url = f"{base_url}/extend?request_id={request_id}"

        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media={"title": title, "poster": poster},
            days_left=days_left,
            quote=SCRUFFY_QUOTES.random(),
            reminder=True,
            extend_url=extend_url,
        )

        message = MessageSchema(
            subject=f"Reminder: {title}",
            recipients=[to_email],
            body=html,
            subtype=MessageType.html,
        )

        await fastmail.send_message(message)
