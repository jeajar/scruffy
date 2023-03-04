import typer
from core.janitor import Janitor
from apis.tautilli import tautulli
from apis.sonarr import sonarr
from apis.radarr import radarr
from json import dumps
from core.email import send_delete_email, send_test_email
from loguru import logger
from core.config import config
import emails

from schemas.emails import EmailValidation

app = typer.Typer()
janitor = Janitor()

@app.command()
def debug():
    things = [
        {1: {"watch": True, "users": ["dude", "dudette", "Mario", "Yves"]}},
        {2: {"watch": False, "users": ["dude", "dudette", "Mario"]}},
        {3: {"watch": True, "users": ["dude", "dudette"]}},
    ]
    things2 = [
        {1: {"watch": True, "users": []}},
        {2: {"watch": True, "users": []}},
        {3: {"watch": True, "users": []}},
    ]
    # if all(season["watch"] for season in [thing.values() for thing in things]):
    #     print("yeah")
    # for t in things:
    #     for s, w in t.items():
    #         print(w['watch'])

    # watch =  [[v['watch'] for _, v in t.items()][0] for t in things2]
    # users =  [[v['users'] for _, v in t.items()][0] for t in things2]
    # print(watch, users)
    # print(all(watch))
    # print(all(not len(others) for others in users))


@app.command()
def email():
    send_test_email()


@app.command()
def tau():
    # history = tautulli._get_children_metadata(81382)
    #print(dumps(tautulli._get_all_plexids(), indent=4))
    print(dumps(tautulli._get_season_rating_keys(81685), indent=4))

@app.command()
def tv():
    tv_shows = janitor.process_tv_requests()

    for series in tv_shows["keep"]:
        sonarr_series = sonarr.get_series(series['request']['media'].get('externalServiceId'))
        print("########### 👀 KEEP SERIES 👀 #############")
        print(sonarr_series.title)
        for data in series['seasons_data']:
            for k, v in data.items():
                print(f"Season {k}:")
                if v['requester_watched']:
                    print("🟢 Watched by Requester")
                else:
                    print("🔴 Watched by Requester")
                have_to = len(v['have_to_watch'])
                if have_to > 0:
                    print(f"🔴 {have_to} users have to watch the series")
                elif have_to == 0:
                    print(f"🟢 All users have watched the series")
                print('\n')
        #print(series['seasons_data'])

    for series in tv_shows["delete"]:
        sonarr_series = sonarr.get_series(series['request']['media'].get('externalServiceId'))
        print("########### 🧹 DELETE SERIES 🧹 #############")
        print(sonarr_series.title)
        for data in series['seasons_data']:
            for k, v in data.items():
                print(f"Season: {k}")
                print("🟢 Watched by Requester")
                print(f"🟢 All users have watched the series")
                print('\n')


@app.command()
def movies():
    movies = janitor.process_movie_requests()
    for movie in movies["keep"]:
        radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
        print("########### KEEP MOVIE #############")
        print(radarr_movie.title)
        if movie['requester_watched']:
            print("🟢 Watched by Requester")
        else:
            print("🔴 Watched by Requester")

        have_to = len(movie['have_to_watch'])
        if have_to > 0:
            print(f"🔴 {have_to} users have to watch the series")
        elif have_to == 0:
            print(f"🟢 All users have watched the series")
        print('\n')

    for movie in movies["delete"]:
        radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
        print("########### DELETE MOVIE #############")
        print(radarr_movie.title)
        if movie['requester_watched']:
            print("🟢 Watched by Requester")
        else:
            print("🔴 Watched by Requester")

        have_to = len(movie['have_to_watch'])
        if have_to > 0:
            print(f"🔴 {have_to} users have to watch the series")
        elif have_to == 0:
            print(f"🟢 All users have watched the series")
        print('\n')

@app.command()
def toute():
    movies = janitor.process_movie_requests()
    for movie in movies["keep"]:
        radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
        print("########### KEEP MOVIE #############")
        print(radarr_movie.title)
        if movie['requester_watched']:
            print("🟢 Watched by Requester")
        else:
            print("🔴 Watched by Requester")

        have_to = len(movie['have_to_watch'])
        if have_to > 0:
            print(f"🔴 {have_to} users have to watch the series")
        elif have_to == 0:
            print(f"🟢 All users have watched the series")
        print('\n')

    for movie in movies["delete"]:
        radarr_movie = radarr.get_movie(movie['request']['media'].get('externalServiceId'))
        print("########### DELETE MOVIE #############")
        print(radarr_movie.title)
        if movie['requester_watched']:
            print("🟢 Watched by Requester")
        else:
            print("🔴 Watched by Requester")

        have_to = len(movie['have_to_watch'])
        if have_to > 0:
            print(f"🔴 {have_to} users have to watch the series")
        elif have_to == 0:
            print(f"🟢 All users have watched the series")
        print('\n')


if __name__ == "__main__":
    app()
