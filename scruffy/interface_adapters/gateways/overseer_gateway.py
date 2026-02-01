"""Gateway adapter for Overseerr API."""

import logging

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)

logger = logging.getLogger(__name__)


class OverseerGateway(RequestRepositoryInterface):
    """Adapter for Overseerr API."""

    def __init__(
        self, base_url: str, api_key: str, http_client: HttpClient | None = None
    ):
        """Initialize Overseerr gateway with base URL and API key."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        self.http_client = http_client or HttpClient()
        logger.debug("Initialized OverseerGateway", extra={"base_url": self.base_url})

    async def status(self) -> bool:
        """Test Overseerr connection status."""
        try:
            await self.http_client.get(
                f"{self.base_url}/api/v1/status", headers=self.headers
            )
            logger.info(
                "Overseerr connection successful", extra={"base_url": self.base_url}
            )
            return True
        except Exception as e:
            logger.warning(
                "Overseerr connection failed",
                extra={"base_url": self.base_url, "error": str(e)},
            )
            return False

    async def get_requests(
        self, status_filter: MediaStatus | None = None
    ) -> list[RequestDTO]:
        """Fetch all media requests from Overseerr using pagination."""
        # Note: Overseerr API doesn't support filtering by MediaStatus directly
        # Filtering is done in the use case layer
        total_requests = await self.get_request_count()
        logger.info(
            "Fetching media requests from Overseerr",
            extra={"total_requests": total_requests},
        )

        all_requests = []
        take = 100
        skip = 0

        while skip < total_requests:
            params = {"take": take, "skip": skip}

            response = await self.http_client.get(
                f"{self.base_url}/api/v1/request",
                headers=self.headers,
                params=params,
            )

            page_results = [
                RequestDTO.from_overseer_response(req)
                for req in response.get("results", [])
            ]
            all_requests.extend(page_results)
            logger.debug(
                "Fetched request page",
                extra={"skip": skip, "take": take, "page_count": len(page_results)},
            )
            skip += take

        logger.info(
            "Completed fetching all requests",
            extra={"total_fetched": len(all_requests)},
        )
        return all_requests

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        logger.info("Deleting request from Overseerr", extra={"request_id": request_id})
        await self.http_client.delete(
            f"{self.base_url}/api/v1/request/{request_id}", headers=self.headers
        )
        logger.debug("Request deleted successfully", extra={"request_id": request_id})

    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        logger.info("Deleting media from Overseerr", extra={"media_id": media_id})
        await self.http_client.delete(
            f"{self.base_url}/api/v1/media/{media_id}", headers=self.headers
        )
        logger.debug("Media deleted successfully", extra={"media_id": media_id})

    async def get_request_count(self) -> int:
        """Get total number of requests."""
        response = await self.http_client.get(
            f"{self.base_url}/api/v1/request/count",
            headers=self.headers,
        )
        count = response["total"]
        logger.debug("Got request count", extra={"count": count})
        return count

    async def user_imported_by_plex_id(self, plex_user_id: int) -> bool:
        """
        Check if a Plex user is imported in Overseerr (has access to our server).

        Returns True if a user with the given plexId exists in Overseerr, False otherwise.
        Raises on Overseerr API/connection errors so callers can fail closed.
        """
        take = 100
        skip = 0
        while True:
            response = await self.http_client.get(
                f"{self.base_url}/api/v1/user",
                headers=self.headers,
                params={"take": take, "skip": skip},
            )
            # Overseerr may return {"results": [...], "pageInfo": {...}} or a list
            if isinstance(response, list):
                results = response
            else:
                results = response.get("results", [])
            for user in results:
                if user.get("plexId") == plex_user_id:
                    logger.debug(
                        "Plex user found in Overseerr",
                        extra={"plex_user_id": plex_user_id},
                    )
                    return True
            result_count = len(results)
            if result_count < take:
                break
            if isinstance(response, list):
                break
            page_info = response.get("pageInfo", {})
            skip += take
            if skip >= page_info.get("total", skip + result_count):
                break
        logger.debug(
            "Plex user not found in Overseerr",
            extra={"plex_user_id": plex_user_id},
        )
        return False
