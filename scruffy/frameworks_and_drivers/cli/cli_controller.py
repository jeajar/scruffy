"""CLI controller for Scruffy application."""

import asyncio
import sys
import warnings

import typer
from rich.console import Console
from rich.table import Table

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync
from scruffy.frameworks_and_drivers.di.container import Container
from scruffy.frameworks_and_drivers.utils.logging import configure_logging, get_logger
from scruffy.interface_adapters.presenters.cli_presenter import CLIPresenter

# Configure logging before anything else
configure_logging(
    level=settings.log_level,
    log_file=settings.log_file,
    loki_enabled=settings.loki_enabled,
    loki_url=str(settings.loki_url) if settings.loki_url else None,
    loki_labels=settings.loki_labels,
)

logger = get_logger(__name__)

app = typer.Typer()

CLI_DEPRECATION_MSG = (
    "The scruffy CLI is deprecated in this release. "
    "Use the web UI and built-in scheduler instead."
)


@app.callback(invoke_without_command=True)
def _cli_deprecation_warning(_ctx: typer.Context) -> None:
    """Emit deprecation warning when CLI is used."""
    warnings.warn(CLI_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    print(CLI_DEPRECATION_MSG, file=sys.stderr)


console = Console(record=True)
_container: Container | None = None


def get_container() -> Container:
    """Get or create dependency injection container."""
    global _container
    if _container is None:
        logger.debug("Creating dependency injection container")
        _container = Container()
    return _container


async def async_check_media():
    """Async function to check media with retention information."""
    container = get_container()
    if not await async_validate():
        raise typer.Exit(1)
    success = False
    error_message: str | None = None
    summary = None
    try:
        result = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )
        summary = {
            "items_checked": len(result),
            "needing_attention": sum(
                1 for r in result if r.retention.remind or r.retention.delete
            ),
        }
        success = True
        return result
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        await asyncio.to_thread(
            record_job_run_sync, "check", success, error_message, summary
        )


async def async_process_media() -> None:
    """Async function to process media."""
    container = get_container()
    if not await async_validate():
        raise typer.Exit(1)
    success = False
    error_message: str | None = None
    summary = None
    try:
        summary = await container.process_media_use_case.execute()
        success = True
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        await asyncio.to_thread(
            record_job_run_sync, "process", success, error_message, summary
        )


async def async_validate() -> bool:
    """Async validate configuration and connections."""
    container = get_container()
    return await container.overseer_gateway.status()


@app.command()
def validate():
    """Validate configuration and show current settings."""
    logger.info("Running validate command")

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
        "Loki Enabled": str(settings.loki_enabled),
    }

    for key, value in settings_to_show.items():
        table.add_row(key, value)

    console.print(table)

    try:
        get_container()
        console.print("[green]✓ Configuration is valid[/green]")
        logger.debug("Configuration validation passed")
    except Exception as e:
        logger.error("Configuration error", extra={"error": str(e)})
        console.print(f"[red]✗ Configuration error: {str(e)}[/red]")
        raise typer.Exit(1)

    connections_valid = asyncio.run(async_validate())

    if connections_valid:
        console.print("[green]✓ Services are ready[/green]")
        logger.info("Validate command completed successfully")
    else:
        logger.error("Services are not ready")
        console.print("[red]✗ Services are not ready[/red]")
        raise typer.Exit(1)


@app.command()
def check():
    """Check media and show what would be processed."""
    logger.info("Running check command")

    results = asyncio.run(async_check_media())

    if not results:
        logger.info("No media found to process")
        console.print("[yellow]No media found to process[/yellow]")
        return

    logger.info("Check completed", extra={"results_count": len(results)})
    table = CLIPresenter.format_media_table(results)
    console.print(table)


@app.command()
def process():
    """Process media and take actions."""
    logger.info("Running process command")
    asyncio.run(async_process_media())
    logger.info("Process command completed")


if __name__ == "__main__":
    app()
