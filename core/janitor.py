from apis.overserr import overseerr
from apis.radarr import radarr
from apis.sonarr import sonarr
from apis.tautilli import tautulli
from loguru import logger


class Janitor(object):
    """The Janitor class is uses the business logic to build list of media entities to delete from Overseerr, Radarr
    Sonarr and from storage, via the *arr APIs.

    The Janitor tries to build on top of existing Overseerr logic, it only scans available requests and don't tries to 
    scan all media in plex, sonarr, radarrr.

    The Janitor works with a media_entity, defined by a "movie" or a tv_show "season". The Janitor does not work with 
    individual tv show episodes.
    """

    def __init__(self) -> None:
        self._movie_keep_requests = []
        self._movie_delete_requests = []
        self._tv_keep_requests = []
        self._tv_delete_requests = []
        self.available_requests = overseerr.get_available_requests()
        self.watchlisted_media = overseerr.get_watchlisted_media()

    def process_movie_requests(self):
        """Process available movie requests.

        Check if the requester and all plex users who have wishlisted the movie have watched it.
        If True, adds the request to _movie_delete_requests, else to _movie_delete_requests
        
        Returns:
            List: A list of Overseerr requests ready to be deleted.
        """
        for request in [r for r in self.available_requests if r.get('type') == "movie"]:
            logger.info(f"Processing Request ID: {request['id']}")
            try:
                ext_id = request['media'].get('externalServiceId')
                title = radarr.get_movie(ext_id).title
                logger.info(f"Title: {title}")
            except Exception as err:
                logger.error(f"TV Show not available in Radarr, deleting request in Overseer: {str(err)}")
                overseerr.delete_request(request['id'])
            must_watch_users = [request['requestedBy'].get('plexId')]
            requester_id = must_watch_users[0]
            request_rating_id = request['media'].get('ratingKey')
            if not request_rating_id:
                logger.error(f"RequestID: {request['id']} has no rating_key watch data could be be gathered")
                continue
            request_media_tmdbid = request['media'].get('tmdbId')
            try:
                must_watch_users.extend(
                    user for user in self.watchlisted_media[request_media_tmdbid] if user not in must_watch_users)
            except KeyError:
                logger.debug(f"Request ID: {request['id']} not watchlisted by any other user")

            logger.debug(f"Must be watched by plex Users: {must_watch_users}")

            is_watched = tautulli.is_entity_played(request_rating_id)
            have_watched_users = [user for user, watch in is_watched.items() if watch]
            logger.debug(f"Have been watched by plex Users: {have_watched_users}")
            logger.debug(f"Request: {request_rating_id} Watched states: {is_watched}")

            requester_watched = False

            if requester_id in have_watched_users:
                requester_watched = True

            if all(user in have_watched_users for user in must_watch_users):
                logger.warning(f'Request ID: {request["id"]} "{title}" will be removed!')
                self._movie_delete_requests.append(
                    {
                        "request": request,
                        "requester_watched": requester_watched,
                        "have_to_watch": []
                     })
                
            else:
                logger.info(f'Request ID: {request["id"]} "{title}" will be kept, not everyone has watched it yet')
                self._movie_keep_requests.append(
                    {
                        "request": request,
                        "requester_watched": requester_watched,
                        "have_to_watch": [user for user in must_watch_users if user not in have_watched_users]
                     })

        logger.info(f"Requests to delete: {len(self._movie_delete_requests)}")
        logger.info(f"Requests to keep: {len(self._movie_keep_requests)}")

        return {"delete": self._movie_delete_requests, "keep": self._movie_keep_requests}

    def process_tv_requests(self):
        """Process available tv requests.

        Check if the requester and all plex users who have watchlisted the tv show
        have watched all episodes in the request.

        If True, adds the request tv show to _tv_delete_requests, else to _tv_delete_requests.
        
        Returns:
            List: A list of Dict: Overseerr requests ready to be deleted with a season value.
        """
        for request in [r for r in self.available_requests if r.get('type') == "tv"]:
            seasons = [season['seasonNumber'] for season in request.get('seasons')]
            logger.debug(f"Season list: {seasons}")
            try:
                ext_id = request['media'].get('externalServiceId')
                title = sonarr.get_series(ext_id).title
                logger.info(f"Title: {title}")
            except Exception as err:
                logger.error(f"TV Show not available in Sonarr, deleting request in Overseer: {str(err)}")
                overseerr.delete_request(request['id'])
                continue
            must_watch_users = [request['requestedBy'].get('plexId')]
            requester_id = must_watch_users[0]
            request_rating_id = request['media'].get('ratingKey')

            if not request_rating_id:
                logger.error(f'RequestID: {request["id"]} "{title}" has no rating_key watch data could be be gathered')
                continue
            request_media_tmdbid = request['media'].get('tmdbId')
            try:
                must_watch_users.extend(user for user in self.watchlisted_media[request_media_tmdbid] if user not in must_watch_users)
            except KeyError:
                logger.debug(f"Request ID: {request['id']} not watchlisted by any other user")

            logger.debug(f"Must be watched by plex Users: {must_watch_users}")

            seasons_status = []
            # Checks for watch status per seson
            for season in seasons:
                try:
                    is_watched = tautulli.is_season_played(request_rating_id, season_number=season)
                except:
                    logger.error("No data available")
                    continue
                season_watched_users = [user for user, watch in is_watched.items() if watch]

                logger.debug(f"Have been watched by plex Users: {season_watched_users}")
                logger.debug(f"Request: {request_rating_id} Watched states: {is_watched}")

                requester_watched = False

                if requester_id in season_watched_users:
                    requester_watched = True

                seasons_status.append({int(season): {
                    "requester_watched": requester_watched,
                    "have_to_watch": [user for user in must_watch_users if user not in season_watched_users]
                    }})
            if not seasons_status:
                continue
            
            requester_watched = all([[value['requester_watched'] for _, value in season.items()][0] for season in seasons_status])
            users_watched = [[value['have_to_watch'] for _, value in season.items()][0] for season in seasons_status]
            logger.warning(f"Requester Watched: {requester_watched}")
            logger.warning(f"Other Users: {users_watched} {all(not len(other) for other in users_watched)}")
            if requester_watched and all(not len(other) for other in users_watched):
                logger.warning(f'Request ID: {request["id"]} "{title}" will be removed!')
                self._tv_delete_requests.append(
                    {
                        "request": request,
                        "seasons_data": seasons_status
                     })
            else:
                logger.info(f'Request ID: {request["id"]} "{title}" will be kept, not everyone has watched it yet')
                self._tv_keep_requests.append(
                                        {
                        "request": request,
                        "seasons_data": seasons_status
                     })

        logger.info(f"Requests to delete: {len(self._tv_delete_requests)}")
        logger.info(f"Requests to keep: {len(self._tv_keep_requests)}")

        return {"delete": self._tv_delete_requests, "keep": self._tv_keep_requests}
