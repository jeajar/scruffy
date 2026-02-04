"""SQLModel for request extensions."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RequestExtensionModel(SQLModel, table=True):
    """
    SQLModel table for tracking extended media requests.

    Each request can only be extended once. When extended, the retention
    calculation adds extension_days to the effective available_since.
    """

    request_id: int = Field(primary_key=True)
    extended_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extended_by_plex_id: int = Field(description="Plex user ID who requested the extension")
