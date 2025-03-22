from rich.console import Console
from rich.table import Table


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
