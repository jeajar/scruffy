import httpx
from core.config import config
from loguru import logger


class OverseerrAPI(object):
    def __init__(self) -> None:
        self.url = config['connectors']['overseerr']['url'].get()
        self.api_key = config['connectors']['overseerr']['api_key'].get()
        self.client = httpx.Client(
            base_url=self.url,
            headers={"X-Api-Key": self.api_key}
        )

    def get_users(self):
        return self.client.get("/user").json()

    def get_user_watchlist(self, user_id):
        return self.client.get(f"/user/{user_id}/watchlist").json()

    def get_user_requests(self, user_id):
        return self.client.get(f"/user/{user_id}/requests").json()
        
    def get_available_requests(self):
        response = self.client.get(
            "/request",
            params={"filter": "available", "take": 100}
            ).json()
        return response.get('results')
        
    def get_media_watch_data(self, media_id):
        return self.client.get(f"/media/{media_id}/watch_data").json()
        
    def get_tv(self, tv_id):
        return self.client.get(f"/tv/{tv_id}").json()
        
    def get_movie(self, movie_id):
        return self.client.get(f"/movie/{movie_id}").json()

    def get_watchlisted_media(self):
        """Build a dictionarry of watchlisted plex users for a tmdbId

        Returns:
            Dict: 
        """
        watchlisted_media = {}
        for user in self.get_users().get('results'):
            watch_items = self.get_user_watchlist(user['id'])
            for item in watch_items['results']:
                if item['tmdbId'] not in watchlisted_media:
                    watchlisted_media.update({item['tmdbId']: [user['plexId']]})
                elif item['tmdbId'] in watchlisted_media:
                    watchlisted_media[item['tmdbId']].append(user['plexId'])
        return watchlisted_media
            
    def delete_request(self, request_id):
        return self.client.delete(f'/request/{request_id}')
    
overseerr = OverseerrAPI()