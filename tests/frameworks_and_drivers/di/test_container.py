"""Tests for DI Container."""

from unittest.mock import Mock, patch

import pytest

from scruffy.frameworks_and_drivers.di.container import Container


@pytest.fixture
def mock_settings():
    """Mock settings store for retention policy (container uses get_retention_policy)."""
    from scruffy.domain.value_objects.retention_policy import RetentionPolicy

    def fake_get_retention_policy():
        return RetentionPolicy(retention_days=30, reminder_days=7)

    with patch(
        "scruffy.frameworks_and_drivers.di.container.get_retention_policy",
        side_effect=fake_get_retention_policy,
    ):
        with patch(
            "scruffy.frameworks_and_drivers.database.settings_store.settings"
        ) as mock:
            mock.overseerr_url = "http://test.com"
            mock.overseerr_api_key = "test-key"
            mock.sonarr_url = "http://test.com"
            mock.sonarr_api_key = "test-key"
            mock.radarr_url = "http://test.com"
            mock.radarr_api_key = "test-key"
            mock.retention_days = 30
            mock.reminder_days = 7
            yield mock


@pytest.fixture
def mock_get_engine():
    """Mock get_engine."""
    with patch("scruffy.frameworks_and_drivers.di.container.get_engine") as mock:
        mock_engine = Mock()
        mock.return_value = mock_engine
        yield mock_engine


class TestContainerInitialization:
    """Tests for Container initialization."""

    def test_container_initialization(self, mock_settings, mock_get_engine):
        """Test container initializes all dependencies."""
        container = Container()

        assert container._http_client is not None
        assert container._email_client is not None
        assert container._database_engine is not None
        assert container._overseer_gateway is not None
        assert container._radarr_gateway is not None
        assert container._sonarr_gateway is not None
        assert container._media_repository is not None
        assert container._reminder_gateway is not None
        assert container._notification_service is not None
        assert container._check_use_case is not None
        assert container._send_reminder_use_case is not None
        assert container._delete_media_use_case is not None
        assert container._retention_calculator is not None
        assert container._process_use_case is not None


class TestContainerProperties:
    """Tests for Container property accessors."""

    def test_container_properties(self, mock_settings, mock_get_engine):
        """Test container properties return correct instances."""
        container = Container()

        assert container.check_media_requests_use_case == container._check_use_case
        assert container.process_media_use_case == container._process_use_case
        assert container.overseer_gateway == container._overseer_gateway
        assert container.retention_calculator == container._retention_calculator


class TestContainerDependencyWiring:
    """Tests for Container dependency wiring."""

    def test_container_wires_dependencies_correctly(
        self, mock_settings, mock_get_engine
    ):
        """Test container wires dependencies correctly."""
        container = Container()

        # Verify gateways use shared HTTP client
        assert container._overseer_gateway.http_client == container._http_client
        assert container._radarr_gateway.http_client == container._http_client
        assert container._sonarr_gateway.http_client == container._http_client

        # Verify media repository uses gateways
        assert container._media_repository.radarr_gateway == container._radarr_gateway
        assert container._media_repository.sonarr_gateway == container._sonarr_gateway

        # Verify use cases use correct repositories
        assert (
            container._check_use_case.request_repository == container._overseer_gateway
        )
        assert container._check_use_case.media_repository == container._media_repository

        # Verify notification service uses email client
        assert container._notification_service.email_client == container._email_client

    def test_container_retention_policy_from_settings(
        self, mock_settings, mock_get_engine
    ):
        """Test container creates retention policy from settings."""
        container = Container()

        assert container._retention_calculator.policy.retention_days == 30
        assert container._retention_calculator.policy.reminder_days == 7
