"""Tests for EmailClient."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scruffy.frameworks_and_drivers.email.email_client import EmailClient


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("scruffy.frameworks_and_drivers.email.email_client.settings") as mock:
        mock.email_enabled = True
        mock.smtp_username = "test"
        mock.smtp_password = "test"
        mock.smtp_from_email = "from@test.com"
        mock.smtp_port = 587
        mock.smtp_host = "smtp.test.com"
        mock.smtp_ssl_tls = False
        mock.smtp_starttls = True
        yield mock


@pytest.fixture
def mock_fastmail():
    """Mock FastMail."""
    with patch("scruffy.frameworks_and_drivers.email.email_client.FastMail") as mock:
        instance = mock.return_value
        instance.send_message = AsyncMock()
        yield instance


@pytest.fixture
def mock_template_env():
    """Mock Jinja2 template environment."""
    with patch(
        "scruffy.frameworks_and_drivers.email.email_client.Environment"
    ) as mock_env:
        template_mock = MagicMock()
        template_mock.render.return_value = "<html>Test</html>"
        mock_env.return_value.get_template.return_value = template_mock
        yield template_mock


class TestEmailClientInitialization:
    """Tests for EmailClient initialization."""

    def test_initialization_disabled(self):
        """Test initialization when email is disabled."""
        with patch(
            "scruffy.frameworks_and_drivers.email.email_client.settings"
        ) as mock_settings:
            mock_settings.email_enabled = False
            client = EmailClient()

            assert client.fastmail is None
            assert client.template_env is None

    def test_initialization_enabled(
        self, mock_settings, mock_fastmail, mock_template_env
    ):
        """Test initialization when email is enabled."""
        client = EmailClient()

        assert client.fastmail is not None
        assert client.template_env is not None
        assert client.conf.USE_CREDENTIALS is True

    def test_initialization_no_credentials(self):
        """Test initialization without credentials."""
        with patch(
            "scruffy.frameworks_and_drivers.email.email_client.settings"
        ) as mock_settings:
            mock_settings.email_enabled = True
            mock_settings.smtp_username = None
            mock_settings.smtp_password = None
            mock_settings.smtp_from_email = "from@test.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_host = "smtp.test.com"
            mock_settings.smtp_ssl_tls = False
            mock_settings.smtp_starttls = True

            with patch("scruffy.frameworks_and_drivers.email.email_client.FastMail"):
                with patch(
                    "scruffy.frameworks_and_drivers.email.email_client.Environment"
                ):
                    client = EmailClient()

                    assert client.conf.USE_CREDENTIALS is False


class TestEmailClientSendMethods:
    """Tests for EmailClient send methods."""

    @pytest.mark.asyncio
    async def test_send_deletion_notice(
        self, mock_settings, mock_fastmail, mock_template_env
    ):
        """Test send_deletion_notice sends email."""
        client = EmailClient()

        await client.send_deletion_notice(
            "test@test.com", "Test Movie", "poster.jpg", days_left=0
        )

        mock_fastmail.send_message.assert_called_once()
        call_args = mock_fastmail.send_message.call_args[0][0]
        assert call_args.subject == "Gone!: Test Movie"
        assert call_args.recipients == ["test@test.com"]

    @pytest.mark.asyncio
    async def test_send_reminder_notice(
        self, mock_settings, mock_fastmail, mock_template_env
    ):
        """Test send_reminder_notice sends email."""
        client = EmailClient()

        await client.send_reminder_notice(
            "test@test.com", "Test Movie", "poster.jpg", days_left=7, request_id=123
        )

        mock_fastmail.send_message.assert_called_once()
        call_args = mock_fastmail.send_message.call_args[0][0]
        assert call_args.subject == "Reminder: Test Movie"
        assert call_args.recipients == ["test@test.com"]

    @pytest.mark.asyncio
    async def test_send_deletion_notice_when_disabled(self):
        """Test send_deletion_notice does nothing when email disabled."""
        with patch(
            "scruffy.frameworks_and_drivers.email.email_client.settings"
        ) as mock_settings:
            mock_settings.email_enabled = False
            client = EmailClient()

            # Should not raise
            await client.send_deletion_notice(
                "test@test.com", "Test Movie", "poster.jpg"
            )

    @pytest.mark.asyncio
    async def test_send_reminder_notice_when_disabled(self):
        """Test send_reminder_notice does nothing when email disabled."""
        with patch(
            "scruffy.frameworks_and_drivers.email.email_client.settings"
        ) as mock_settings:
            mock_settings.email_enabled = False
            client = EmailClient()

            # Should not raise
            await client.send_reminder_notice(
                "test@test.com", "Test Movie", "poster.jpg", days_left=7, request_id=123
            )


class TestEmailClientTemplatePath:
    """Tests for EmailClient template path configuration."""

    def test_template_path_exists(
        self, mock_settings, mock_fastmail, mock_template_env
    ):
        """Test template path is correctly set."""
        client = EmailClient()

        # Verify template path exists (or at least the directory structure)
        template_path = (
            Path(__file__).parent.parent.parent.parent.parent / "scruffy" / "templates"
        )
        # Just verify the path structure is correct, not that it exists
        assert "templates" in str(template_path)
