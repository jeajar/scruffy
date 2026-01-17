from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Media:
    """Core business entity representing media information."""

    id: int
    title: str
    available: bool
    available_since: datetime | None
    size_on_disk: int
    poster: str
    seasons: list[int]

    def is_available(self) -> bool:
        """Check if media is available."""
        return self.available and self.available_since is not None
