import typer
from apis.sonarr import sonarr
from apis.radarr import radarr

from core.email import send_email
from core.janitor import Janitor
from datetime import datetime

from rich import print
from rich.console import Console
from rich.table import Table


app = typer.Typer(add_completion=False)
janitor = Janitor()

now = datetime.now()

# @app.command()
# def email():
#     movies = janitor.process_movie_requests()
#     simple_data = []
#     for movie in movies['delete']:
#         title = radarr.get_movie(movie['request']['media'].get('externalServiceId')).title
#         over_id = movie['request']['media'].get('tmdbId')
#         url = f"https://requests.jmax.tech/movie/{over_id}"
#         simple_data.append({"title": title, "url": url})
#     send_email(to_emails=["jeanmaxim.desjardins@gmail.com"], subject_template="hello", movie_data=simple_data)


@app.command(name="tv", help="Process all Overseer TV requests")
def tv_requests(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all requests"),
    delete: bool = typer.Option(False, "--delete", "-D", help="DANGER!: delete overseer request, sonarr entry and media on filesystem")
):
    tv_shows = janitor.process_tv_requests()
    table = Table(title="Delete TV Series")
    table.add_column("Title", justify="left", style="cyan")
    table.add_column("Delete?", justify="center", style="cyan")
    table.add_column("Requester Watched", justify="center")
    table.add_column("Others Watched?", justify="center")
    table.add_column("Age", justify="center")
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
                requested_at = datetime.strptime(series['request']["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                request_age = now-requested_at
                age = str(request_age.days)+" days old"

                table.add_row(title, delete, requester_watched, others, age)

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
            requested_at = datetime.strptime(series['request']["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
            request_age = now-requested_at
            age = str(request_age.days)+" days old"

            table.add_row(title, delete, requester_watched, others, age)


    if delete:
        for series in tv_shows["delete"]:
            janitor.delete_series(series)

    console = Console()
    console.print(table)


@app.command(name="movies", help="Process all Overseer movie requests")
def movie_requests(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all requests"),
    delete: bool = typer.Option(False, "--delete", "-D", help="DANGER!: delete overseer request, radarr entry and media on filesystem")
    ):
    movies = janitor.process_movie_requests()

    table = Table(title="Delete Movies")
    table.add_column("Title", justify="left", style="cyan")
    table.add_column("Delete?", justify="center", style="cyan")
    table.add_column("Requester Watched", justify="center")
    table.add_column("Others Watched (Watchlisted)?", justify="center")
    table.add_column("Age", justify="center")
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
                    others = f"[bold red]{have_to} user have to watch[/bold red]"
                else:
                    others = f"[bold red]{have_to} users have to watch[/bold red]"
            elif have_to == 0:
                others = f"[bold green]YES[/bold green]"

            requested_at = datetime.strptime(movie['request']["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
            request_age = now-requested_at
            age = str(request_age.days)+" days old"

            table.add_row(title, delete, requester_watched, others, age)

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
                others = f"[bold red]{have_to} user have to watch[/bold red]"
            else:
                others = f"[bold red]{have_to} users have to watch[/bold red]"
        elif have_to == 0:
            others = f"[bold green]YES[/bold green]"

        requested_at = datetime.strptime(movie['request']["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        request_age = now-requested_at
        age = str(request_age.days)+" days old"
            
        table.add_row(title, delete, requester_watched, others, age)

    if delete:
        for movie in movies["delete"]:
            janitor.delete_movie(movie)

    console = Console()
    console.print(table)

@app.command(name="delete-tv", help="Delete a TV series")
def delete_tv(
    tv_id: int = typer.Argument(..., help="Series ID from Overseer. hint: in the URL")
    ):
    series = janitor.process_series(tv_id=tv_id)
    typer.echo(series)
    delete = typer.confirm(f"Are you sure you want to delete TV series: {series['name']} and all associated media files?")
    if delete:
        janitor.delete_series(series=series)
    else:
        typer.echo("Cancelling...")


@app.command(name="delete-movie", help="Delete a movie")
def delete_tv(
    movie_id: int = typer.Argument(..., help="Movie ID from Overseer. hint: in the URL")
    ):
    movie = janitor.process_movie(movie_id=movie_id)
    delete = typer.confirm(f"Are you sure you want to delete movie: {movie['name']} and all associated media files?")
    if delete:
        typer.echo(movie)
        janitor.delete_movie(movie=movie)
    else:
        typer.echo("Cancelling...")

if __name__ == "__main__":
    app()
