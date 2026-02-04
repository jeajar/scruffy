import random
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.utils.quotes import scruffy_quotes


class EmailClient:
    """FastMail wrapper for sending emails."""

    def __init__(self):
        """Initialize email client with settings."""
        if not settings.email_enabled:
            self.fastmail = None
            self.template_env = None
            return

        # Set empty strings if credentials not provided
        username = settings.smtp_username or ""
        password = settings.smtp_password or ""
        use_credentials = bool(username and password)
        self.conf = ConnectionConfig(
            MAIL_USERNAME=username,
            MAIL_PASSWORD=password,
            MAIL_FROM_NAME="Scruffy, the Janitor",
            MAIL_FROM=settings.smtp_from_email,
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_host,
            MAIL_SSL_TLS=settings.smtp_ssl_tls,
            MAIL_STARTTLS=settings.smtp_starttls,
            USE_CREDENTIALS=use_credentials,
        )

        self.fastmail = FastMail(self.conf)
        # Templates are in scruffy/templates
        templates_path = Path(__file__).parent.parent.parent / "templates"
        self.template_env = Environment(loader=FileSystemLoader(templates_path))

    async def send_deletion_notice(
        self, to_email: str, title: str, poster: str, days_left: int = 0
    ) -> None:
        """Send deletion notice email."""
        if not self.fastmail:
            return

        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media={"title": title, "poster": poster},
            days_left=days_left,
            quote=random.choice(scruffy_quotes),
            reminder=False,
        )

        message = MessageSchema(
            subject=f"Gone!: {title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)

    async def send_reminder_notice(
        self,
        to_email: str,
        title: str,
        poster: str,
        days_left: int,
        request_id: int,
    ) -> None:
        """Send reminder notice email."""
        if not self.fastmail:
            return

        base_url = settings.app_base_url.rstrip("/")
        extend_url = f"{base_url}/extend?request_id={request_id}"

        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media={"title": title, "poster": poster},
            days_left=days_left,
            quote=random.choice(scruffy_quotes),
            reminder=True,
            extend_url=extend_url,
        )

        message = MessageSchema(
            subject=f"Reminder: {title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)
