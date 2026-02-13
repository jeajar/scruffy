"""Tests for job run store."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.database.database import (
    get_engine,
    reset_engine_for_testing,
)
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync


@pytest.fixture
def _temp_db():
    """Provide temp dir for DB and patch settings."""
    reset_engine_for_testing()
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "scruffy.frameworks_and_drivers.database.database.settings"
        ) as mock_settings:
            mock_settings.data_dir = Path(tmpdir)
            yield


def test_record_job_run_sync_persists_summary(_temp_db):
    """Test that record_job_run_sync stores summary JSON."""
    summary = {
        "reminders_sent": [{"email": "a@b.com", "title": "X", "days_left": 3}],
        "needs_attention": [],
        "deletions": [],
    }
    record_job_run_sync("process", True, None, summary)

    engine = get_engine()
    with Session(engine) as session:
        rows = list(session.exec(select(JobRunModel)))
    assert len(rows) == 1
    assert rows[0].job_type == "process"
    assert rows[0].success is True
    assert rows[0].summary is not None
    parsed = json.loads(rows[0].summary)
    assert parsed["reminders_sent"] == summary["reminders_sent"]
    assert parsed["deletions"] == summary["deletions"]


def test_record_job_run_sync_without_summary(_temp_db):
    """Test that record_job_run_sync with no summary stores None."""
    record_job_run_sync("check", True, None)

    engine = get_engine()
    with Session(engine) as session:
        rows = list(session.exec(select(JobRunModel)))
    assert len(rows) == 1
    assert rows[0].summary is None
