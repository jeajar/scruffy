from rich.table import Table

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.services.retention_calculator import RetentionResult


class CLIPresenter:
    """Formats output for CLI display."""

    @staticmethod
    def format_media_table(
        results: list[tuple[MediaRequest, Media]],
        retention_results: list[RetentionResult],
    ) -> Table:
        """Format media results as a Rich table."""
        table = Table(title="Media Status")
        table.add_column("Id", style="white")
        table.add_column("Title", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Days Left", style="magenta")
        table.add_column("User", style="yellow")
        table.add_column("Action", style="green")

        for (request, media), retention in zip(results, retention_results):
            action = (
                "[red]Delete[/red]"
                if retention.delete
                else "[yellow]Remind[/yellow]"
                if retention.remind
                else "[green]Keep[/green]"
            )

            seasons = ", ".join(
                str(f"s{season:02d}") for season in media.seasons
            )
            title = f"{media.title} {seasons}" if seasons else media.title

            table.add_row(
                str(request.request_id),
                title,
                request.media_type.value,
                str(retention.days_left),
                request.user_email,
                action,
            )

        return table
