import typer
from apis.sonarr import sonarr
from apis.radarr import radarr

from core.email import send_email
from core.janitor import Janitor

from rich import print
from rich.console import Console
from rich.table import Table


app = typer.Typer()
janitor = Janitor()


@app.command()
def email():
    movies = janitor.process_movie_requests()
    simple_data = []
    for movie in movies['delete']:
        title = radarr.get_movie(movie['request']['media'].get('externalServiceId')).title
        over_id = movie['request']['media'].get('tmdbId')
        url = f"https://requests.jmax.tech/movie/{over_id}"
        simple_data.append({"title": title, "url": url})
    send_email(to_emails=["jeanmaxim.desjardins@gmail.com"], subject_template="hello", movie_data=simple_data)

    
@app.command()
def tv(
    show_all: bool = typer.Option(False, "-all", "-", help="Show all requests")
):
    tv_shows = janitor.process_tv_requests()
    table = Table(title="Delete TV Series")
    table.add_column("Title", justify="left", style="cyan")
    table.add_column("Delete?", justify="center", style="cyan")
    table.add_column("Requester Watched", justify="center")
    table.add_column("Others Watched?", justify="center")
    if show_all:
        for series in tv_shows["keep"]:
            sonarr_series = sonarr.get_series(series['request']['media'].get('externalServiceId'))
            title = sonarr_series.title
            delete = "[bold red]NO[/bold red]"
            for data in series['seasons_data']:
                for k, v in data.items():
                    title += f" - season: {k}"
                    if v['requester_watched']:
                        requester_watched = "[bold green]YES[/bold green]"
                    else:
                        requester_watched = "[bold red]NO[/bold red]"
                    have_to = len(v['have_to_watch'])
                    if have_to > 0:
                        if len(v['have_to_watch']) == 1:
                            others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
                        else:
                            others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
                    elif have_to == 0:
                        others = f"[bold green]YES[/bold green]"
                table.add_row(title, delete, requester_watched, others)

    for series in tv_shows["delete"]:
        sonarr_series = sonarr.get_series(series['request']['media'].get('externalServiceId'))
        title = sonarr_series.title
        delete = "[bold green]YES[/bold green]"
        for data in series['seasons_data']:
            for k, v in data.items():
                title += f" - season: {k}"
                if v['requester_watched']:
                    requester_watched = "[bold green]YES[/bold green]"
                else:
                    requester_watched = "[bold red]NO[/bold red]"
                have_to = len(v['have_to_watch'])
                if have_to > 0:
                    if len(v['have_to_watch']) == 1:
                        others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
                    else:
                        others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
                elif have_to == 0:
                    others = f"[bold green]YES[/bold green]"
            table.add_row(title, delete, requester_watched, others)

    console = Console()
    console.print(table)


@app.command()
def movies(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all requests")
    ):
    movies = janitor.process_movie_requests()

    table = Table(title="Delete Movies")
    table.add_column("Title", justify="left", style="cyan")
    table.add_column("Delete?", justify="center", style="cyan")
    table.add_column("Requester Watched", justify="center")
    table.add_column("Others Watched (Watchlisted)?", justify="center")
    if show_all:
        for movie in movies["keep"]:
            radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
            title = radarr_movie.title
            delete = "[bold red]NO[/bold red]"
            if movie['requester_watched']:
                requester_watched = "[bold green]YES[/bold green]"
            else:
                requester_watched = "[bold red]NO[/bold red]"
            have_to = len(movie['have_to_watch'])
            if have_to > 0:
                if len(movie['have_to_watch']) == 1:
                    others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
                else:
                    others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
            elif have_to == 0:
                others = f"[bold green]YES[/bold green]"
            table.add_row(title, delete, requester_watched, others)

    for movie in movies["delete"]:
        radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
        title = radarr_movie.title
        delete = "[bold green]YES[/bold green]"
        if movie['requester_watched']:
            requester_watched = "[bold green]YES[/bold green]"
        else:
            requester_watched = "[bold red]NO[/bold red]"
        have_to = len(movie['have_to_watch'])
        if have_to > 0:
            if len(movie['have_to_watch']) == 1:
                others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
            else:
                others = f"[bold red]{have_to} user(s) have to watch[/bold red]"
        elif have_to == 0:
            others = f"[bold green]YES[/bold green]"
        table.add_row(title, delete, requester_watched, others)


    console = Console()
    console.print(table)

if __name__ == "__main__":
    app()
