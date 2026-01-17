"""Tests for CLIPresenter."""

import pytest
from rich.table import Table

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.interface_adapters.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)
from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO
from scruffy.interface_adapters.dtos.request_dto import RequestDTO
from scruffy.interface_adapters.presenters.cli_presenter import CLIPresenter


@pytest.fixture
def sample_result_delete():
    """Sample MediaCheckResultDTO with delete action."""
    request = RequestDTO(
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
    media = MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=None,
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    retention = RetentionResultDTO(remind=True, delete=True, days_left=-5)
    return MediaCheckResultDTO(request=request, media=media, retention=retention)


@pytest.fixture
def sample_result_remind():
    """Sample MediaCheckResultDTO with remind action."""
    request = RequestDTO(
        user_id=2,
        user_email="test2@example.com",
        type="movie",
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=None,
        media_status=MediaStatus.AVAILABLE,
        media_id=100,
        external_service_id=102,
        seasons=[],
    )
    media = MediaInfoDTO(
        id=2,
        title="Another Movie",
        available=True,
        available_since=None,
        size_on_disk=2000000,
        poster="",
        seasons=[],
    )
    retention = RetentionResultDTO(remind=True, delete=False, days_left=7)
    return MediaCheckResultDTO(request=request, media=media, retention=retention)


@pytest.fixture
def sample_result_tv():
    """Sample MediaCheckResultDTO for TV show with seasons."""
    request = RequestDTO(
        user_id=3,
        user_email="tv@example.com",
        type="tv",
        request_id=3,
        request_status=RequestStatus.APPROVED,
        updated_at=None,
        media_status=MediaStatus.AVAILABLE,
        media_id=101,
        external_service_id=103,
        seasons=[1, 2],
    )
    media = MediaInfoDTO(
        id=3,
        title="Test Series",
        available=True,
        available_since=None,
        size_on_disk=3000000,
        poster="",
        seasons=[1, 2],
    )
    retention = RetentionResultDTO(remind=False, delete=False, days_left=15)
    return MediaCheckResultDTO(request=request, media=media, retention=retention)


def test_format_media_table_creates_table(sample_result_delete):
    """Test format_media_table creates Rich Table."""
    table = CLIPresenter.format_media_table([sample_result_delete])

    assert isinstance(table, Table)
    assert table.title == "Media Status"


def test_format_media_table_columns(sample_result_delete):
    """Test format_media_table has correct columns."""
    table = CLIPresenter.format_media_table([sample_result_delete])

    # Check column names
    column_names = [col.header for col in table.columns]
    assert "Id" in column_names
    assert "Title" in column_names
    assert "Type" in column_names
    assert "Days Left" in column_names
    assert "User" in column_names
    assert "Action" in column_names


def test_format_media_table_delete_action(sample_result_delete):
    """Test format_media_table shows Delete action."""
    table = CLIPresenter.format_media_table([sample_result_delete])

    # Check that Delete action is shown
    rows = list(table.rows)
    assert len(rows) == 1
    # Action column should contain "Delete" (with Rich markup)
    action_cell = rows[0][5]  # Action is last column
    assert "Delete" in str(action_cell) or "[red]" in str(action_cell)


def test_format_media_table_remind_action(sample_result_remind):
    """Test format_media_table shows Remind action."""
    table = CLIPresenter.format_media_table([sample_result_remind])

    rows = list(table.rows)
    assert len(rows) == 1
    action_cell = rows[0][5]
    assert "Remind" in str(action_cell) or "[yellow]" in str(action_cell)


def test_format_media_table_keep_action(sample_result_tv):
    """Test format_media_table shows Keep action."""
    table = CLIPresenter.format_media_table([sample_result_tv])

    rows = list(table.rows)
    assert len(rows) == 1
    action_cell = rows[0][5]
    assert "Keep" in str(action_cell) or "[green]" in str(action_cell)


def test_format_media_table_season_formatting(sample_result_tv):
    """Test format_media_table formats seasons correctly."""
    table = CLIPresenter.format_media_table([sample_result_tv])

    rows = list(table.rows)
    title_cell = rows[0][1]  # Title is second column
    title_str = str(title_cell)
    # Should include season formatting
    assert "s01" in title_str.lower() or "s1" in title_str.lower()


def test_format_media_table_multiple_results(sample_result_delete, sample_result_remind, sample_result_tv):
    """Test format_media_table handles multiple results."""
    table = CLIPresenter.format_media_table([
        sample_result_delete,
        sample_result_remind,
        sample_result_tv,
    ])

    rows = list(table.rows)
    assert len(rows) == 3


def test_format_media_table_empty_list():
    """Test format_media_table handles empty list."""
    table = CLIPresenter.format_media_table([])

    assert isinstance(table, Table)
    rows = list(table.rows)
    assert len(rows) == 0
