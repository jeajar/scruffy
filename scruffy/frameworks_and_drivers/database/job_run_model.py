"""SQLModel for job run history (check/process executions)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class JobRunModel(SQLModel, table=True):
    """
    Record of a job execution (check or process).

    job_type: "check" (scan media) or "process" (send reminders + delete).
    finished_at: when the job completed.
    success: whether the job completed without exception.
    error_message: exception message if failed.
    """

    id: int | None = Field(default=None, primary_key=True)
    job_type: str = Field(index=True)  # "check" | "process"
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool = Field()
    error_message: str | None = Field(default=None)
