"""SQLModel for scheduled jobs (check/process)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ScheduleJobModel(SQLModel, table=True):
    """
    Stored schedule for a Scruffy job (check or process).

    cron_expression: standard 5-field cron (minute hour day month dow).
    job_type: "check" or "process".
    """

    id: int | None = Field(default=None, primary_key=True)
    job_type: str = Field(index=True, unique=True)  # "check" | "process"
    cron_expression: str = Field(min_length=9)  # e.g. "0 */6 * * *"
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
