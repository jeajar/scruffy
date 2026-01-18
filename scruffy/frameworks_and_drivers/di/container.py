"""Dependency injection container for Scruffy application."""

import logging

from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.email.email_client import EmailClient
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.media_repository_composite import (
    MediaRepositoryComposite,
)
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
        self._email_client = EmailClient()
        self._database_engine = get_engine()

        # Gateways (interface adapters)
        logger.debug("Creating gateways")
        self._overseer_gateway = OverseerGateway(
            str(settings.overseerr_url), settings.overseerr_api_key, self._http_client
        )
        self._radarr_gateway = RadarrGateway(
            str(settings.radarr_url), settings.radarr_api_key, self._http_client
        )
        self._sonarr_gateway = SonarrGateway(
            str(settings.sonarr_url), settings.sonarr_api_key, self._http_client
        )
        self._media_repository = MediaRepositoryComposite(
            self._radarr_gateway, self._sonarr_gateway
        )
        self._reminder_gateway = ReminderGateway(self._database_engine)
        self._notification_service = EmailNotificationService(self._email_client)

        # Use cases
        logger.debug("Creating use cases")
        self._check_use_case = CheckMediaRequestsUseCase(
            self._overseer_gateway, self._media_repository
        )
        self._send_reminder_use_case = SendReminderUseCase(
            self._reminder_gateway, self._notification_service
        )
        self._delete_media_use_case = DeleteMediaUseCase(
            self._media_repository,
            self._overseer_gateway,
            self._notification_service,
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
    def retention_calculator(self) -> RetentionCalculator:
        """Get retention calculator."""
        return self._retention_calculator
