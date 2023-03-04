from loguru import logger

import emails
from emails.template import JinjaTemplate
from pathlib import Path
from typing import Any, Dict

from core.config import config
from core.settings import settings

from schemas.emails import EmailContent, EmailValidation

def send_email(
        email_to: str,
        subject_template: str = "",
        html_template: str = "",
        environment: Dict[str, Any] = {},
    ) -> None:
    assert config['email'], logger.error('Email configuration missing')
    message = emails.Message(
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(config['email']['from_name'].get(), config['email']['from'].get())
    )
    smtp_options = {
        "host": config['email']['host'].get(),
        "port": config['email']['port'].get(),
    }
    if config['email']['tls'].get():
        smtp_options['tls'] = config['email']['tls'].get()
    if config['email']['user'].get():
        smtp_options['user'] = config['email']['user'].get()
    if config['email']['password'].get():
        smtp_options['password'] = config['email']['password'].get()
    print(smtp_options, email_to, environment)
    
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logger.info(f"send email result: {response}")

def send_delete_email(data: EmailValidation) -> None:
    subject = f"{data.subject}"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "delete_notification.html") as f:
        template_str = f.read()
    send_email(
        email_to=data.email,
        subject_template=subject,
        html_template=template_str,
        environment=data.delete_data
    )

def send_test_email() -> None:
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "delete_notification.html") as f:
        template_str = f.read()
    send_email(
        email_to=config['email']['user'].get(),
        subject_template="Test",
        html_template=template_str,
        environment={
            "project_name": "Scruffy",
            "valid_minutes": int(90),
            "link": "https://example.com",
        }
    )
