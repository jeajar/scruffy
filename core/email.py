from loguru import logger

import smtplib
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from pathlib import Path
import jinja2

from pathlib import Path
from typing import Any, Dict

from core.config import config
from core.settings import settings


def _render_template(movie_data):
    ''' renders a Jinja template into HTML '''
    templateLoader = jinja2.FileSystemLoader(settings.EMAIL_TEMPLATES_DIR)
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template("delete_notification.html.j2")
    return templ.render(movie_data=movie_data)

def send_email(
        to_emails: list = [],
        subject_template: str = "",
        movie_data: Dict[str, Any] = {},
    ) -> None:
    msg = MIMEMultipart('alternative')
    msg['From']    = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM_EMAIL))
    msg['Subject'] = subject_template
    msg['Bcc']      = ','.join(to_emails)
    msg.attach(MIMEText(_render_template(movie_data), 'html'))
    mailserver = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    mailserver.ehlo("scruffy")
    mailserver.starttls()
    mailserver.ehlo("scruffy")
    mailserver.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
    try:
        logger.info('sending email...')
        mailserver.sendmail(
            settings.EMAIL_FROM_EMAIL,
            to_emails, msg.as_string())
    except Exception as err:
        logger.error('Error sending email')
        logger.exception(str(err))
    finally:
        mailserver.quit()


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
