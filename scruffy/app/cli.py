import asyncio
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from scruffy.app.app import MediaManager
from scruffy.infra import (
    MediaInfoDTO,
    OverseerRepository,
    RadarrRepository,
    ReminderRepository,
    RequestDTO,
    SonarrRepository,
    settings,
)
from scruffy.services import EmailService

app = typer.Typer()
console = Console(record=True)
_manager: Optional[MediaManager] = None


def get_manager() -> MediaManager:
    global _manager
    if _manager is None:
        _manager = MediaManager(
            overseer=OverseerRepository(
                str(settings.overseerr_url), settings.overseerr_api_key
            ),
            sonarr=SonarrRepository(str(settings.sonarr_url), settings.sonarr_api_key),
            radarr=RadarrRepository(str(settings.radarr_url), settings.radarr_api_key),
            reminder_repository=ReminderRepository(),
            email_service=EmailService(),
        )
    return _manager


async def async_check_media() -> list[tuple[RequestDTO, MediaInfoDTO]]:
    """Async function to check media"""
    if not await async_validate():
        raise typer.Exit(1)
    manager = get_manager()
    return await manager.check_requests()


async def async_process_media() -> None:
    """Async function to process media"""
    if not await async_validate():
        raise typer.Exit(1)
    manager = get_manager()
    await manager.process_media()


async def async_validate() -> bool:
    """Async validate configuration and connections"""
    manager = get_manager()
    return await manager.validate_connections()


@app.command()
def validate():
    """Validate configuration and show current settings"""
    table = Table(title="Scruffy Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Add settings, mask sensitive values
    settings_to_show = {
        "Overseerr URL": str(settings.overseerr_url),
        "Sonarr URL": str(settings.sonarr_url),
        "Radarr URL": str(settings.radarr_url),
        "Email Enabled": str(settings.email_enabled),
        "Retention Days": str(settings.retention_days),
        "Reminder Days": str(settings.reminder_days),
        "Log Level": settings.log_level,
        "Data Directory": settings.data_dir,
    }

    for key, value in settings_to_show.items():
        table.add_row(key, value)

    console.print(table)

    try:
        get_manager()
        console.print("[green]✓ Configuration is valid[/green]")
    except Exception as e:
        console.print(f"[red]✗ Configuration error: {str(e)}[/red]")
        raise typer.Exit(1)

    connections_valid = asyncio.run(async_validate())

    if connections_valid:
        console.print("[green]✓ Services are ready[/green]")
    else:
        console.print("[red]✗ Services are not ready[/red]")
        raise typer.Exit(1)


@app.command()
def check(ctx: typer.Context):
    """Check media and show what would be processed"""
    try:
        results = asyncio.get_event_loop().run_until_complete(async_check_media())
    except RuntimeError:
        # If we're in a running event loop (tests), create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(async_check_media())
        loop.close()

    if not results:
        console.print("[yellow]No media found to process[/yellow]")
        return

    table = Table(title="Media Status")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Age (days)", style="magenta")
    table.add_column("Action", style="green")

    for request, media_info in results:
        age = (datetime.now(timezone.utc) - media_info.available_since).days
        action = (
            "[red]Delete[/red]"
            if age >= settings.retention_days
            else "[yellow]Remind[/yellow]"
            if age >= (settings.retention_days - settings.reminder_days)
            else "[green]Keep[/green]"
        )

        seasons = ", ".join(str(f"s{season:02d}") for season in media_info.seasons)
        table.add_row(f"{media_info.title} {seasons}", request.type, str(age), action)

    console.print(table)


@app.command()
def process(ctx: typer.Context):
    """Process media and take actions"""
    try:
        asyncio.get_event_loop().run_until_complete(async_process_media())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_process_media())
        loop.close()


if __name__ == "__main__":
    app()
