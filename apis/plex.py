from plexapi.server import PlexServer
from plexapi.video import Show
from core.config import config

url = config['connectors']['plex']['url'].get()
token = config['connectors']['plex']['token'].get()

plex_server = PlexServer(baseurl=url, token=token)
#plex_show = Show(plex_server)