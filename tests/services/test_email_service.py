from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi_mail import MessageSchema
from pydantic import SecretStr

from scruffy.infra import MediaInfoDTO
from scruffy.services.email_service import EmailService


@pytest.fixture
def mock_settings():
    with patch("scruffy.services.email_service.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.smtp_username = "test"
        mock_settings.smtp_password = "test"
        mock_settings.smtp_from_email = "from@test.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_ssl_tls = False
        mock_settings.smtp_starttls = True
        yield mock_settings


@pytest.fixture
def mock_fastmail():
    with patch("scruffy.services.email_service.FastMail") as mock:
        instance = mock.return_value
        instance.send_message = AsyncMock()
        yield instance


@pytest.fixture
def mock_template():
    with patch("scruffy.services.email_service.Environment") as mock_env:
        template_mock = MagicMock()
        template_mock.render.return_value = "<html>Test</html>"
        mock_env.return_value.get_template.return_value = template_mock
        yield template_mock


@pytest.fixture
def media_info():
    return MediaInfoDTO(
        title="Test Movie",
        available=True,
        available_since=None,
        poster="test.jpg",
        seasons=[1],
        size_on_disk=1000,
        id=1,
    )


def test_service_initialization_disabled(mock_settings):
    mock_settings.email_enabled = False
    service = EmailService()
    assert not hasattr(service, "fastmail")


def test_service_initialization_no_credentials(mock_settings):
    mock_settings.smtp_username = None
    mock_settings.smtp_password = None
    service = EmailService()
    assert service.conf.USE_CREDENTIALS is False


def test_service_initialization_with_credentials(mock_settings):  # noqa: ARG001
    service = EmailService()
    assert service.conf.USE_CREDENTIALS is True
    assert service.conf.MAIL_USERNAME == "test"
    assert service.conf.MAIL_PASSWORD == SecretStr("test")


@pytest.mark.asyncio
async def test_send_deletion_notice(
    mock_settings,  # noqa: ARG001
    mock_fastmail,
    mock_template,  # noqa: ARG001
    media_info,
):
    service = EmailService()
    await service.send_deletion_notice("test@test.com", media_info)

    mock_fastmail.send_message.assert_called_once()
    call_args = mock_fastmail.send_message.call_args[0][0]
    assert isinstance(call_args, MessageSchema)
    assert call_args.subject == f"Gone!: {media_info.title}"
    assert call_args.recipients == ["test@test.com"]


@pytest.mark.asyncio
async def test_send_reminder_notice(
    mock_settings,  # noqa: ARG001
    mock_fastmail,
    mock_template,  # noqa: ARG001
    media_info,
):
    service = EmailService()
    days_left = 7
    await service.send_reminder_notice("test@test.com", media_info, days_left)

    mock_fastmail.send_message.assert_called_once()
    call_args = mock_fastmail.send_message.call_args[0][0]
    assert isinstance(call_args, MessageSchema)
    assert call_args.subject == f"Reminder: {media_info.title}"
    assert call_args.recipients == ["test@test.com"]


def test_template_rendering(mock_settings, mock_template, media_info):  # noqa: ARG001
    service = EmailService()
    mock_template.render.assert_not_called()

    service.template_env.get_template("base.html.j2")
    mock_template.render.assert_not_called()

    # Verify template path exists
    template_path = Path(__file__).parent.parent.parent / "scruffy" / "templates"
    assert template_path.exists()
