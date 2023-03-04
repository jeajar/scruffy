from arrapi import RadarrAPI
from core.config import config

url = config['connectors']['radarr']['url'].get()
api_key = config['connectors']['radarr']['api_key'].get()

radarr = RadarrAPI(url, api_key)