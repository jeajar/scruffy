#!/usr/bin/env python3
"""Send a real test reminder email for a media request (e.g. Shawshank) to a given address.

Use this to test the reminder email and the "I need more time!" link.

Usage (from repo root, with .env configured for email):
  uv run --env-file .env python scripts/send_test_reminder.py
"""

import asyncio
import logging
import sys

from scruffy.frameworks_and_drivers.di.container import Container

# Title to match (case-insensitive, substring)
TITLE_MATCH = "shawshank"
TO_EMAIL = "jeanmaxim.desjardins@gmail.com"
# Days left shown in email (typical reminder window)
DAYS_LEFT = 7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    container = Container()
    try:
        results = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )
        match = None
        for r in results:
            if TITLE_MATCH in r.media.title.lower():
                match = r
                break
        if not match:
            logger.error(
                "No media request found with title containing %r. Available titles: %s",
                TITLE_MATCH,
                [r.media.title for r in results],
            )
            sys.exit(1)
        assert match is not None  # Narrow type after guard
        logger.info(
            "Sending test reminder for %s (request_id=%s) to %s",
            match.media.title,
            match.request.request_id,
            TO_EMAIL,
        )
        await container.notification_service.send_reminder_notice(
            TO_EMAIL,
            match.media,
            days_left=match.retention.days_left
            if match.retention.days_left > 0
            else DAYS_LEFT,
            request_id=match.request.request_id,
        )
        logger.info(
            "Test reminder sent. Check %s; extend link will be APP_BASE_URL/extend?request_id=%s",
            TO_EMAIL,
            match.request.request_id,
        )
    finally:
        await container.aclose()


if __name__ == "__main__":
    asyncio.run(main())
