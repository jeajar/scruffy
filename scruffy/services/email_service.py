from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader

from scruffy.infra import MediaInfoDTO, settings


class EmailService:
    def __init__(self):
        if not settings.EMAIL_ENABLED:
            return
        use_credentials = bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM_NAME="Scruffy, the Janitor",
            MAIL_FROM=settings.SMTP_FROM_EMAIL,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_SSL_TLS=settings.SMTP_SSL_TLS,
            MAIL_STARTTLS=settings.SMTP_STARTTLS,
            USE_CREDENTIALS=use_credentials,
        )

        self.fastmail = FastMail(self.conf)
        self.template_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent / "templates")
        )

    async def send_deletion_notice(self, to_email: str, media: MediaInfoDTO) -> None:
        template = self.template_env.get_template("delete.html.j2")
        html = template.render(media=media)

        message = MessageSchema(
            subject=f"Content Deletion Notice: {media.title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)

    async def send_reminder_notice(
        self, to_email: str, media: MediaInfoDTO, days_left: int
    ) -> None:
        template = self.template_env.get_template("reminder.html.j2")
        html = template.render(media=media, days_left=days_left)

        message = MessageSchema(
            subject=f"Content Expiration Reminder: {media.title}",
            recipients=[to_email],
            body=html,
            subtype="html",
        )

        await self.fastmail.send_message(message)
