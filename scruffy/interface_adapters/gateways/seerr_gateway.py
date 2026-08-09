"""Gateway adapter for Seerr API."""

import logging

from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpRequestError,
    IHttpClient,
)
from scruffy.interface_adapters.interfaces.settings_provider_interface import (
    ISettingsProvider,
)
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)

logger = logging.getLogger(__name__)


class SeerrGateway(RequestRepositoryInterface):
    """Adapter for Seerr API."""

    def __init__(
        self,
        settings_provider: ISettingsProvider,
        http_client: IHttpClient,
    ):
        """Initialize Seerr gateway with settings provider for runtime config."""
        self._settings_provider = settings_provider
        self.http_client = http_client
        logger.debug("Initialized SeerrGateway")

    def _get_config(self) -> tuple[str, dict]:
        """Get base_url and headers from settings (DB + env fallback)."""
        config = self._settings_provider.get_services_config()
        base_url = config.seerr_url.rstrip("/")
        api_key = config.seerr_api_key or ""
        headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        return base_url, headers

    async def status(self) -> bool:
        """Test Seerr connection status."""
        base_url, headers = self._get_config()
        try:
            await self.http_client.get(f"{base_url}/api/v1/status", headers=headers)
            logger.info("Seerr connection successful", extra={"base_url": base_url})
            return True
        except Exception as e:
            logger.warning(
                "Seerr connection failed",
                extra={"base_url": base_url, "error": str(e)},
            )
            return False

    async def get_requests(self) -> list[RequestDTO]:
        """Fetch all media requests from Seerr using pagination."""
        base_url, headers = self._get_config()
        take = 100
        skip = 0

        # First page: get data and infer total if API returns it (avoids extra count call)
        response = await self.http_client.get(
            f"{base_url}/api/v1/request",
            headers=headers,
            params={"take": take, "skip": skip},
        )
        page_results = [
            RequestDTO.from_seerr_response(req) for req in response.get("results", [])
        ]
        all_requests = list(page_results)

        page_info = response.get("pageInfo") if isinstance(response, dict) else {}
        total_requests = None
        if isinstance(page_info, dict) and "total" in page_info:
            total_requests = page_info["total"]
        elif isinstance(response, dict) and "total" in response:
            total_requests = response["total"]

        if total_requests is None:
            total_requests = await self.get_request_count()

        logger.info(
            "Fetching media requests from Seerr",
            extra={"total_requests": total_requests},
        )
        logger.debug(
            "Fetched request page",
            extra={"skip": skip, "take": take, "page_count": len(page_results)},
        )
        skip += take

        while skip < total_requests:
            response = await self.http_client.get(
                f"{base_url}/api/v1/request",
                headers=headers,
                params={"take": take, "skip": skip},
            )
            page_results = [
                RequestDTO.from_seerr_response(req)
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

    async def get_request(self, request_id: int) -> RequestDTO | None:
        """Fetch a single request by ID. Returns None if not found."""
        base_url, headers = self._get_config()
        try:
            response = await self.http_client.get(
                f"{base_url}/api/v1/request/{request_id}",
                headers=headers,
            )
            return RequestDTO.from_seerr_response(response)
        except Exception as e:
            logger.debug(
                "Request not found or error fetching",
                extra={"request_id": request_id, "error": str(e)},
            )
            return None

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        base_url, headers = self._get_config()
        logger.info("Deleting request from Seerr", extra={"request_id": request_id})
        await self.http_client.delete(
            f"{base_url}/api/v1/request/{request_id}", headers=headers
        )
        logger.debug("Request deleted successfully", extra={"request_id": request_id})

    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        base_url, headers = self._get_config()
        logger.info("Deleting media from Seerr", extra={"media_id": media_id})
        await self.http_client.delete(
            f"{base_url}/api/v1/media/{media_id}", headers=headers
        )
        logger.debug("Media deleted successfully", extra={"media_id": media_id})

    async def get_request_count(self) -> int:
        """Get total number of requests."""
        base_url, headers = self._get_config()
        response = await self.http_client.get(
            f"{base_url}/api/v1/request/count",
            headers=headers,
        )
        count = response["total"]
        logger.debug("Got request count", extra={"count": count})
        return count

    async def user_imported_by_plex_id(self, plex_user_id: int) -> bool:
        """
        Check if a Plex user is imported in Seerr (has access to our server).

        Returns True if a user with the given plexId exists in Seerr, False otherwise.
        Raises on Seerr API/connection errors so callers can fail closed.
        """
        base_url, headers = self._get_config()
        take = 100
        skip = 0
        while True:
            response = await self.http_client.get(
                f"{base_url}/api/v1/user",
                headers=headers,
                params={"take": take, "skip": skip},
            )
            # Seerr may return {"results": [...], "pageInfo": {...}} or a list
            if isinstance(response, list):
                results = response
            else:
                results = response.get("results", [])
            for user in results:
                if user.get("plexId") == plex_user_id:
                    logger.debug(
                        "Plex user found in Seerr",
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
            "Plex user not found in Seerr",
            extra={"plex_user_id": plex_user_id},
        )
        return False

    async def get_user_by_plex_id(self, plex_user_id: int) -> dict | None:
        """
        Get the Seerr user object for a Plex user ID.

        Returns the user dict (with id, permissions, etc.) or None if not found.
        Used to check admin/role from Seerr (e.g. permissions & ADMIN).
        Returns None when Seerr is unreachable (connection/timeout errors).
        """
        base_url, headers = self._get_config()
        take = 100
        skip = 0
        try:
            while True:
                response = await self.http_client.get(
                    f"{base_url}/api/v1/user",
                    headers=headers,
                    params={"take": take, "skip": skip},
                )
                if isinstance(response, list):
                    results = response
                else:
                    results = response.get("results", [])
                for user in results:
                    if user.get("plexId") == plex_user_id:
                        logger.debug(
                            "Seerr user found by Plex ID",
                            extra={"plex_user_id": plex_user_id},
                        )
                        return user
                result_count = len(results)
                if result_count < take:
                    break
                if isinstance(response, list):
                    break
                page_info = response.get("pageInfo", {})
                skip += take
                if skip >= page_info.get("total", skip + result_count):
                    break
            return None
        except HttpRequestError as e:
            logger.warning(
                "Seerr unreachable when resolving user by Plex ID",
                extra={
                    "plex_user_id": plex_user_id,
                    "base_url": base_url,
                    "error": str(e),
                },
            )
            return None

    # Seerr Permission.ADMIN = 2 (from server/lib/permissions.ts)
    ADMIN_PERMISSION = 2

    @staticmethod
    def is_seerr_admin(user: dict | None) -> bool:
        """
        Return True if the Seerr user has admin permission.

        Seerr uses a permissions bitmask (see server/lib/permissions in Seerr).
        ADMIN = 2 in Seerr's Permission enum.
        """
        if not user:
            return False
        perms = user.get("permissions", 0)
        if isinstance(perms, int):
            return (perms & SeerrGateway.ADMIN_PERMISSION) != 0
        return False
