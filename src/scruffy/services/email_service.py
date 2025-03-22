import random
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader

from scruffy.infra import MediaInfoDTO, settings
from scruffy.quotes import scruffy_quotes


class EmailService:
    def __init__(self):
        if not settings.email_enabled:
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
        self.template_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent / "templates")
        )

    async def send_deletion_notice(self, to_email: str, media: MediaInfoDTO) -> None:
        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media=media,
            days_left=0,
            quote=random.choice(scruffy_quotes),
            reminder=False,
        )

        message = MessageSchema(
            subject=f"Gone!: {media.title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)

    async def send_reminder_notice(
        self, to_email: str, media: MediaInfoDTO, days_left: int
    ) -> None:
        template = self.template_env.get_template("base.html.j2")
        html = template.render(
            media=media,
            days_left=days_left,
            quote=random.choice(scruffy_quotes),
            reminder=True,
        )

        message = MessageSchema(
            subject=f"Reminder: {media.title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)
