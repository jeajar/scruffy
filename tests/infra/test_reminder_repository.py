import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from scruffy.infra.reminder_repository import ReminderRepository
from scruffy.models.reminder_model import Reminder


@pytest.fixture(name="engine")
def engine_fixture():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def repository(engine):
    """Create a ReminderRepository instance with test database."""
    return ReminderRepository(engine=engine)


def test_has_reminder_when_not_exists(repository):
    """Test has_reminder returns False when reminder doesn't exist."""
    assert repository.has_reminder(request_id=1) is False


def test_has_reminder_when_exists(repository, engine):
    """Test has_reminder returns True when reminder exists."""
    # Arrange
    with Session(engine) as session:
        reminder = Reminder(request_id=1, user_id=1)
        session.add(reminder)
        session.commit()

    # Act & Assert
    assert repository.has_reminder(request_id=1) is True


def test_add_reminder(repository):
    """Test adding a new reminder."""
    # Act
    repository.add_reminder(request_id=1, user_id=1)

    # Assert
    assert repository.has_reminder(request_id=1) is True


def test_add_reminder_multiple_times(repository):
    """Test adding multiple reminders."""
    # Act
    repository.add_reminder(request_id=1, user_id=1)
    repository.add_reminder(request_id=2, user_id=1)

    # Assert
    assert repository.has_reminder(request_id=1) is True
    assert repository.has_reminder(request_id=2) is True


def test_has_reminder_with_multiple_entries(repository):
    """Test has_reminder with multiple entries in database."""
    # Arrange
    repository.add_reminder(request_id=1, user_id=1)
    repository.add_reminder(request_id=2, user_id=1)

    # Act & Assert
    assert repository.has_reminder(request_id=1) is True
    assert repository.has_reminder(request_id=2) is True
    assert repository.has_reminder(request_id=3) is False
