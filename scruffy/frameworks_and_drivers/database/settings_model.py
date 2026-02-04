"""SQLModel for admin settings (key-value store)."""

from sqlmodel import Field, SQLModel


class SettingsModel(SQLModel, table=True):
    """
    Key-value store for admin-configurable settings.

    Used for extension_days and other settings that can be overridden
    via the admin UI instead of environment variables.
    """

    key: str = Field(primary_key=True, description="Setting key, e.g. extension_days")
    value: str = Field(description="Setting value stored as string")
