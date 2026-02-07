"""Seed sample job run entries for testing the Jobs UI. Uses same DB as the API (respects DATA_DIR/.env)."""

import sys
from pathlib import Path

# Ensure project root is on path so scruffy can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync

# Check job: items checked and needing attention
record_job_run_sync(
    "check",
    True,
    None,
    {"items_checked": 24, "needing_attention": 5},
)
record_job_run_sync(
    "check",
    True,
    None,
    {"items_checked": 0, "needing_attention": 0},
)

# Process job: reminders only
record_job_run_sync(
    "process",
    True,
    None,
    {
        "reminders": [
            {"email": "alice@example.com", "title": "Inception", "days_left": 5},
            {"email": "bob@example.com", "title": "The Wire S1", "days_left": 2},
        ],
        "deletions": [],
    },
)

# Process job: deletions only
record_job_run_sync(
    "process",
    True,
    None,
    {
        "reminders": [],
        "deletions": [
            {"email": "charlie@example.com", "title": "Old Documentary"},
            {"email": "dana@example.com", "title": "Expired Movie (2020)"},
        ],
    },
)

# Process job: both reminders and deletions
record_job_run_sync(
    "process",
    True,
    None,
    {
        "reminders": [
            {"email": "eve@example.com", "title": "Breaking Bad S1", "days_left": 1},
        ],
        "deletions": [
            {"email": "frank@example.com", "title": "Retention Expired Show"},
        ],
    },
)

# One failed run (no summary)
record_job_run_sync("process", False, "Connection refused to Radarr")

print("Seeded sample job runs. Open Admin → Jobs to see the UI.")
