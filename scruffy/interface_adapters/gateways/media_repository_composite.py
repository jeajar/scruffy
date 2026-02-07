from scruffy.domain.value_objects.media_type import MediaType
from scruffy.interface_adapters.gateways.radarr_gateway import RadarrGateway
from scruffy.interface_adapters.gateways.sonarr_gateway import SonarrGateway
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)


class MediaRepositoryComposite(MediaRepositoryInterface):
    """Composite repository that delegates to Radarr or Sonarr based on media type."""

    def __init__(self, radarr_gateway: RadarrGateway, sonarr_gateway: SonarrGateway):
        """Initialize with Radarr and Sonarr gateways."""
        self.radarr_gateway = radarr_gateway
        self.sonarr_gateway = sonarr_gateway

    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get media from appropriate gateway based on type."""
        if media_type == MediaType.MOVIE:
            return await self.radarr_gateway.get_media(
                external_service_id, media_type, seasons
            )
        return await self.sonarr_gateway.get_media(
            external_service_id, media_type, seasons
        )

    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete media from appropriate gateway based on type."""
        if media_type == MediaType.MOVIE:
            await self.radarr_gateway.delete_media(
                external_service_id, media_type, seasons
            )
        else:
            await self.sonarr_gateway.delete_media(
                external_service_id, media_type, seasons
            )
