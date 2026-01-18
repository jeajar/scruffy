"""Tests for CLI controller."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from scruffy.frameworks_and_drivers.cli.cli_controller import app


@pytest.fixture
def runner():
    """Create CliRunner instance."""
    return CliRunner()


@pytest.fixture
def mock_container():
    """Mock Container."""
    container = Mock()
    container.check_media_requests_use_case = Mock()
    container.process_media_use_case = Mock()
    container.overseer_gateway = Mock()
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("scruffy.frameworks_and_drivers.cli.cli_controller.settings") as mock:
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
        mock.data_dir = "/tmp"
        yield mock


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_validate_command_success(mock_get_container, runner, mock_container, mock_settings):
    """Test validate command succeeds."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=True)

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "Configuration is valid" in result.stdout
    assert "Services are ready" in result.stdout


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_validate_command_service_failure(mock_get_container, runner, mock_container, mock_settings):
    """Test validate command fails when services are not ready."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=False)

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 1
    assert "Services are not ready" in result.stdout


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_check_command_with_results(mock_get_container, runner, mock_container, mock_settings):
    """Test check command with media results."""
    from scruffy.use_cases.dtos.media_check_result_dto import (
        MediaCheckResultDTO,
        RetentionResultDTO,
    )
    from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
    from scruffy.use_cases.dtos.request_dto import RequestDTO
    from scruffy.domain.value_objects.media_status import MediaStatus
    from scruffy.domain.value_objects.request_status import RequestStatus

    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=True)
    
    request_dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=None,
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )
    media_dto = MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=None,
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    retention_dto = RetentionResultDTO(remind=True, delete=False, days_left=7)
    result_dto = MediaCheckResultDTO(
        request=request_dto,
        media=media_dto,
        retention=retention_dto,
    )
    
    mock_container.check_media_requests_use_case.execute_with_retention = AsyncMock(
        return_value=[result_dto]
    )

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert "Test Movie" in result.stdout or "Media Status" in result.stdout


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_check_command_no_results(mock_get_container, runner, mock_container, mock_settings):
    """Test check command with no media results."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=True)
    mock_container.check_media_requests_use_case.execute_with_retention = AsyncMock(
        return_value=[]
    )

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert "No media found to process" in result.stdout


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_process_command_success(mock_get_container, runner, mock_container, mock_settings):
    """Test process command succeeds."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=True)
    mock_container.process_media_use_case.execute = AsyncMock()

    result = runner.invoke(app, ["process"])

    assert result.exit_code == 0
    mock_container.process_media_use_case.execute.assert_called_once()


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_check_command_validation_failure(mock_get_container, runner, mock_container, mock_settings):
    """Test check command fails when validation fails."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=False)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1


@patch("scruffy.frameworks_and_drivers.cli.cli_controller.get_container")
def test_process_command_validation_failure(mock_get_container, runner, mock_container, mock_settings):
    """Test process command fails when validation fails."""
    mock_get_container.return_value = mock_container
    mock_container.overseer_gateway.status = AsyncMock(return_value=False)

    result = runner.invoke(app, ["process"])

    assert result.exit_code == 1
