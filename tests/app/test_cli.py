from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from scruffy.app.cli import app
from scruffy.infra.constants import MediaStatus, RequestStatus
from scruffy.infra.data_transfer_objects import MediaInfoDTO, RequestDTO


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_settings():
    with patch("scruffy.app.cli.settings") as mock:
        mock.overseerr_url = "http://test.com"
        mock.overseerr_api_key = "test-key"
        mock.sonarr_url = "http://test.com"
        mock.sonarr_api_key = "test-key"
        mock.radarr_url = "http://test.com"
        mock.radarr_api_key = "test-key"
        mock.email_enabled = True
        mock.retention_days = 30
        mock.reminder_days = 7
        mock.log_level = "INFO"
        yield mock


@pytest.fixture
def sample_request():
    return RequestDTO(
        user_id=1,
        user_email="test@test.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC) - timedelta(days=25),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=1,
        seasons=[],
    )


@pytest.fixture
def sample_media():
    return MediaInfoDTO(
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=25),
        poster="test.jpg",
        seasons=[],
        size_on_disk=1000,
        id=1,
    )


@patch("scruffy.app.cli.async_check_media")
def test_check_command_with_media(mock_check, runner, sample_request, sample_media):
    async def mock_results():
        return [(sample_request, sample_media)]

    mock_check.side_effect = mock_results

    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Test Movie" in result.stdout
    assert "movie" in result.stdout
    assert "25" in result.stdout
    assert "Remind" in result.stdout


@patch("scruffy.app.cli.async_check_media")
def test_check_command_no_media(mock_check, runner):
    async def mock_results():
        return []

    mock_check.side_effect = mock_results

    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "No media found to process" in result.stdout


@patch("scruffy.app.cli.async_process_media")
def test_process_command_success(mock_process, runner):
    async def mock_processing():
        return None

    mock_process.side_effect = mock_processing

    result = runner.invoke(app, ["process"])
    assert result.exit_code == 0
