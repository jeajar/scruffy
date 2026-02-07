from rich.table import Table

from scruffy.use_cases.dtos.media_check_result_dto import MediaCheckResultDTO


class CLIPresenter:
    """Formats output for CLI display."""

    @staticmethod
    def format_media_table(results: list[MediaCheckResultDTO]) -> Table:
        """Format media results as a Rich table."""
        table = Table(title="Media Status")
        table.add_column("Id", style="white")
        table.add_column("Title", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Days Left", style="magenta")
        table.add_column("User", style="yellow")
        table.add_column("Action", style="green")

        for result in results:
            action = (
                "[red]Delete[/red]"
                if result.retention.delete
                else "[yellow]Remind[/yellow]"
                if result.retention.remind
                else "[green]Keep[/green]"
            )

            seasons = ", ".join(
                str(f"s{season:02d}") for season in result.media.seasons
            )
            title = f"{result.media.title} {seasons}" if seasons else result.media.title

            # Get media type from request DTO
            media_type_value = "movie" if result.request.type == "movie" else "tv"

            table.add_row(
                str(result.request.request_id),
                title,
                media_type_value,
                str(result.retention.days_left),
                result.request.user_email,
                action,
            )

        return table
