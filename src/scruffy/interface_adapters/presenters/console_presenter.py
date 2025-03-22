from datetime import UTC, datetime

from rich.console import Console
from rich.table import Table

from ...infra import settings


class ConsolePresenter:
    """Presenter for displaying output to the console."""

    def __init__(self, record: bool = True) -> None:
        self.console = Console(record=record)

    def show_configuration(self, settings_dict: dict[str, str]) -> None:
        """Display configuration in a table format."""
        table = Table(title="Scruffy Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        for key, value in settings_dict.items():
            table.add_row(key, value)

        self.console.print(table)

    def show_success(self, message: str) -> None:
        """Display a success message."""
        self.console.print(f"[green]{message}[/green]")

    def show_error(self, message: str) -> None:
        """Display an error message."""
        self.console.print(f"[red]{message}[/red]")

    def show_warning(self, message: str) -> None:
        """Display a warning message."""
        self.console.print(f"[yellow]{message}[/yellow]")

    def show_media_status(self, media_results: list) -> None:
        """Display media status in a table format."""
        if not media_results:
            self.show_warning("No media found to process")
            return

        table = Table(title="Media Status")
        table.add_column("Title", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Age (days)", style="magenta")
        table.add_column("Action", style="green")

        for request, media_info in media_results:
            age = (datetime.now(UTC) - media_info.available_since).days
            action = (
                "[red]Delete[/red]"
                if age >= settings.retention_days
                else "[yellow]Remind[/yellow]"
                if age >= (settings.retention_days - settings.reminder_days)
                else "[green]Keep[/green]"
            )

            seasons = ", ".join(f"s{season:02d}" for season in media_info.seasons)
            table.add_row(
                f"{media_info.title} {seasons}", request.type, str(age), action
            )

        self.console.print(table)
