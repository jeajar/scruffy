from arrapi import SonarrAPI
from core.config import config

url = config['connectors']['sonarr']['url'].get()
api_key = config['connectors']['sonarr']['api_key'].get()

sonarr = SonarrAPI(url, api_key)