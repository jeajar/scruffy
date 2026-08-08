"""Shared poster-extraction helper for Radarr/Sonarr image payloads."""


def extract_poster_url(images: list[dict]) -> str | None:
    """Get the poster's remote URL from a Radarr/Sonarr `images` list, if present."""
    return next(
        (img["remoteUrl"] for img in images if img.get("coverType") == "poster"),
        None,
    )
