"""Tests for one-off database migrations."""

from sqlmodel import Session

from scruffy.frameworks_and_drivers.database.database import (
    _migrate_rename_seerr_settings_keys,
)
from scruffy.frameworks_and_drivers.database.settings_model import SettingsModel


def _value(session: Session, key: str) -> str:
    row = session.get(SettingsModel, key)
    assert row is not None, f"expected a row for key {key!r}"
    return row.value


def test_migrate_renames_overseerr_keys_to_seerr(in_memory_engine):
    """Existing services.overseerr_* rows are renamed to services.seerr_*."""
    with Session(in_memory_engine) as session:
        session.add(
            SettingsModel(key="services.overseerr_url", value="http://old:5055")
        )
        session.add(SettingsModel(key="services.overseerr_api_key", value="old-key"))
        session.commit()

    _migrate_rename_seerr_settings_keys(in_memory_engine)

    with Session(in_memory_engine) as session:
        assert session.get(SettingsModel, "services.overseerr_url") is None
        assert session.get(SettingsModel, "services.overseerr_api_key") is None
        assert _value(session, "services.seerr_url") == "http://old:5055"
        assert _value(session, "services.seerr_api_key") == "old-key"


def test_migrate_renames_seer_keys_to_seerr(in_memory_engine):
    """Existing services.seer_* rows (the misspelled interim key) are renamed to services.seerr_*."""
    with Session(in_memory_engine) as session:
        session.add(SettingsModel(key="services.seer_url", value="http://old:5055"))
        session.add(SettingsModel(key="services.seer_api_key", value="old-key"))
        session.commit()

    _migrate_rename_seerr_settings_keys(in_memory_engine)

    with Session(in_memory_engine) as session:
        assert session.get(SettingsModel, "services.seer_url") is None
        assert session.get(SettingsModel, "services.seer_api_key") is None
        assert _value(session, "services.seerr_url") == "http://old:5055"
        assert _value(session, "services.seerr_api_key") == "old-key"


def test_migrate_keeps_existing_seer_value_and_drops_stale_overseerr_row(
    in_memory_engine,
):
    """If services.seer_url already has a value, it wins and the stale overseerr row is dropped."""
    with Session(in_memory_engine) as session:
        session.add(
            SettingsModel(key="services.overseerr_url", value="http://old:5055")
        )
        session.add(SettingsModel(key="services.seer_url", value="http://new:5055"))
        session.commit()

    _migrate_rename_seerr_settings_keys(in_memory_engine)

    with Session(in_memory_engine) as session:
        assert session.get(SettingsModel, "services.overseerr_url") is None
        assert session.get(SettingsModel, "services.seer_url") is None
        assert _value(session, "services.seerr_url") == "http://new:5055"


def test_migrate_is_a_noop_on_fresh_db(in_memory_engine):
    """Running the migration with no rows present does nothing and does not error."""
    _migrate_rename_seerr_settings_keys(in_memory_engine)

    with Session(in_memory_engine) as session:
        assert session.get(SettingsModel, "services.seerr_url") is None


def test_migrate_is_idempotent(in_memory_engine):
    """Running the migration twice is safe."""
    with Session(in_memory_engine) as session:
        session.add(
            SettingsModel(key="services.overseerr_url", value="http://old:5055")
        )
        session.commit()

    _migrate_rename_seerr_settings_keys(in_memory_engine)
    _migrate_rename_seerr_settings_keys(in_memory_engine)

    with Session(in_memory_engine) as session:
        assert _value(session, "services.seerr_url") == "http://old:5055"
