import httpx
from core.config import config
from loguru import logger

class TautulliException(Exception):
    pass

class TautulliAPI(object):
    def __init__(self) -> None:
        self.url = config['connectors']['tautulli']['url'].get()
        self.api_key = config['connectors']['tautulli']['api_key'].get()
        self.client = httpx.Client(
            base_url=self.url,
            headers={"X-Api-Key": self.api_key}
        )
        self.user_ids = self._get_all_plexids()

    def _get(self, method):
        return self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": method
            }).json()

    def _get_all_plexids(self):
        response = self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": "get_users"
            }).json()
        return [int(user['user_id']) for user in response['response']['data']]

    def get_activiy(self):
        return self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": "get_activity"
            }).json()


    def get_tv_history(self, rating_key):
        """TV Shows take grandparent_rating_key
        Season is parent_rating_key
        Episode is rating_key
        """
        return self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": "get_history",
                "grandparent_rating_key": rating_key
            }).json()

    def get_history(self, rating_key, is_show=False, is_season=False):
        """TV Shows take grandparent_rating_key
        Season is parent_rating_key
        Episode is rating_key
        """
        rating_cat = 'grandparent_rating_key' if is_show else 'parent_key' if is_season  else 'rating_key'
        return self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": "get_history",
                rating_cat: rating_key
            }).json()

    def get_status(self):
        return self.client.get("/status").json()

    def _get_children_metadata(self, rating_key):
        return self.client.get(
            "/api/v2",
            params={
                "apikey": self.api_key,
                "cmd": "get_children_metadata",
                'rating_key': rating_key
            }).json()

    def _get_season_rating_keys(self, rating_key):
        """Check who has played a whole season for a tv season

        Returns:
            Dict: A dict of media_index with dict of title, seaonson rating_key
        """
        data = {}
        for season in self._get_children_metadata(rating_key)['response']['data']['children_list']:
            if season.get('media_index'):
                data.update({int(season['media_index']): {"title": season['title'], "rating_key": season['rating_key']}})
        return data

    def is_entity_played(self, rating_key):
        """Check who has played an entity (movie or episode)

        Returns:
            Dict: A dict of plex_user_id with a bool as_watched attribute
        """
        data = {}
        for play in self.get_history(rating_key)['response']['data']['data']:
            plex_id = play['user_id']
            if play['watched_status'] == 1:
                watched = True
            else:
                watched = False
            if data.get(plex_id) and not watched:
                # Don't want to override with not watched if the user watched multiple times
                continue
            else:
                data.update({int(plex_id): watched})

        # If the user is not in the watch data, he hasn't seen it.
        for plex_id in self.user_ids:
            if plex_id not in data.keys():
                data.update({int(plex_id): False})
        logger.debug(data)
        return data

    def is_season_played(self, rating_key, season_number:1):
        """Check who has played an entire season.

        If any episode has no playback data, returns false.
        """
        data = self._get_season_rating_keys(rating_key=rating_key)
        season_key = data.get(season_number)['rating_key']
        episodes = [ep['rating_key'] for ep in self._get_children_metadata(season_key)['response']['data']['children_list']]
        season_data = {}
        season_watch = [self.is_entity_played(ep) for ep in episodes]
        for play in season_watch:
            season_data.update(play)
        logger.debug(season_data)
        return season_data


tautulli = TautulliAPI()
