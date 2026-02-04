"""Dependency injection container for Scruffy application."""

import logging

from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.settings_store import SettingsProvider
from scruffy.frameworks_and_drivers.email.email_client import EmailClient
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.media_repository_composite import (
    MediaRepositoryComposite,
)
from scruffy.interface_adapters.gateways.extension_gateway import ExtensionGateway
from scruffy.interface_adapters.gateways.overseer_gateway import OverseerGateway
from scruffy.interface_adapters.gateways.radarr_gateway import RadarrGateway
from scruffy.interface_adapters.gateways.reminder_gateway import ReminderGateway
from scruffy.interface_adapters.gateways.sonarr_gateway import SonarrGateway
from scruffy.interface_adapters.notifications.email_notification_service import (
    EmailNotificationService,
)
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase
from scruffy.use_cases.process_media_use_case import ProcessMediaUseCase
from scruffy.use_cases.request_extension_use_case import RequestExtensionUseCase
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase

logger = logging.getLogger(__name__)


class Container:
    """Dependency injection container."""

    def __init__(self):
        """Initialize container and wire up dependencies."""
        logger.info("Initializing dependency injection container")

        # Framework dependencies
        logger.debug("Creating framework dependencies")
        self._http_client = HttpClient()
        self._settings_provider = SettingsProvider()
        self._email_client = EmailClient(self._settings_provider)
        self._database_engine = get_engine()

        # Gateways (interface adapters) - use SettingsProvider for DB-backed config
        logger.debug("Creating gateways")
        self._overseer_gateway = OverseerGateway(
            self._settings_provider, self._http_client
        )
        self._radarr_gateway = RadarrGateway(
            self._settings_provider, self._http_client
        )
        self._sonarr_gateway = SonarrGateway(
            self._settings_provider, self._http_client
        )
        self._media_repository = MediaRepositoryComposite(
            self._radarr_gateway, self._sonarr_gateway
        )
        self._reminder_gateway = ReminderGateway(self._database_engine)
        self._extension_gateway = ExtensionGateway(self._database_engine)
        self._notification_service = EmailNotificationService(self._email_client)

        # Use cases
        logger.debug("Creating use cases")
        self._check_use_case = CheckMediaRequestsUseCase(
            self._overseer_gateway,
            self._media_repository,
            self._extension_gateway,
        )
        self._send_reminder_use_case = SendReminderUseCase(
            self._reminder_gateway, self._notification_service
        )
        self._delete_media_use_case = DeleteMediaUseCase(
            self._media_repository,
            self._overseer_gateway,
            self._notification_service,
        )
        self._request_extension_use_case = RequestExtensionUseCase(
            self._extension_gateway,
            self._overseer_gateway,
        )

        retention_policy = RetentionPolicy(
            retention_days=settings.retention_days,
            reminder_days=settings.reminder_days,
        )
        self._retention_calculator = RetentionCalculator(retention_policy)

        self._process_use_case = ProcessMediaUseCase(
            self._check_use_case,
            self._send_reminder_use_case,
            self._delete_media_use_case,
            retention_policy,
        )

        logger.info(
            "Container initialized successfully",
            extra={
                "retention_days": settings.retention_days,
                "reminder_days": settings.reminder_days,
                "email_enabled": settings.email_enabled,
            },
        )

    async def aclose(self) -> None:
        """Close shared resources (e.g. HTTP client). Call on application shutdown."""
        await self._http_client.aclose()
        logger.debug("Container closed")

    @property
    def check_media_requests_use_case(self) -> CheckMediaRequestsUseCase:
        """Get check media requests use case."""
        return self._check_use_case

    @property
    def process_media_use_case(self) -> ProcessMediaUseCase:
        """Get process media use case."""
        return self._process_use_case

    @property
    def overseer_gateway(self) -> OverseerGateway:
        """Get Overseerr gateway."""
        return self._overseer_gateway

    @property
    def radarr_gateway(self) -> RadarrGateway:
        """Get Radarr gateway."""
        return self._radarr_gateway

    @property
    def sonarr_gateway(self) -> SonarrGateway:
        """Get Sonarr gateway."""
        return self._sonarr_gateway

    @property
    def retention_calculator(self) -> RetentionCalculator:
        """Get retention calculator."""
        return self._retention_calculator

    @property
    def request_extension_use_case(self) -> RequestExtensionUseCase:
        """Get request extension use case."""
        return self._request_extension_use_case

    @property
    def extension_gateway(self) -> ExtensionGateway:
        """Get extension gateway."""
        return self._extension_gateway
