"""Tests for EmailNotificationService."""

from unittest.mock import AsyncMock, Mock

import pytest

from scruffy.frameworks_and_drivers.email.email_client import EmailClient
from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO
from scruffy.interface_adapters.notifications.email_notification_service import (
    EmailNotificationService,
)


@pytest.fixture
def mock_email_client():
    """Mock EmailClient."""
    return Mock(spec=EmailClient)


@pytest.fixture
def service(mock_email_client):
    """Create EmailNotificationService instance."""
    return EmailNotificationService(mock_email_client)


@pytest.fixture
def sample_media_dto():
    """Sample MediaInfoDTO for testing."""
    return MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=None,
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )


@pytest.mark.asyncio
async def test_send_reminder_notice(service, mock_email_client, sample_media_dto):
    """Test send_reminder_notice calls email client."""
    mock_email_client.send_reminder_notice = AsyncMock()

    await service.send_reminder_notice("test@example.com", sample_media_dto, days_left=7)

    mock_email_client.send_reminder_notice.assert_called_once_with(
        "test@example.com",
        sample_media_dto.title,
        sample_media_dto.poster,
        7,
    )


@pytest.mark.asyncio
async def test_send_deletion_notice(service, mock_email_client, sample_media_dto):
    """Test send_deletion_notice calls email client."""
    mock_email_client.send_deletion_notice = AsyncMock()

    await service.send_deletion_notice("test@example.com", sample_media_dto)

    mock_email_client.send_deletion_notice.assert_called_once_with(
        "test@example.com",
        sample_media_dto.title,
        sample_media_dto.poster,
        days_left=0,
    )


def test_service_initialization_default():
    """Test service initialization with default email client."""
    service = EmailNotificationService()

    # Should not raise error
    assert service.email_client is not None
