from typing import Any, Iterable, Optional

from pardner.services import BaseTransferService
from pardner.services.base import UnsupportedVerticalException
from pardner.verticals import Vertical


class StravaTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Strava's API.
    See API documentation: https://developers.strava.com/docs/reference/
    """

    _authorization_url = 'https://www.strava.com/oauth/authorize'
    _token_url = 'https://www.strava.com/oauth/token'

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        verticals: set[Vertical] = set(),
    ) -> None:
        super().__init__(
            service_name='Strava',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            supported_verticals={
                Vertical.ExerciseAction,
                Vertical.FeedPost,
                Vertical.Follower,
            },
            verticals=verticals,
        )

    def fetch_token(
        self, code: Optional[str] = None, authorization_response: Optional[str] = None
    ) -> dict[str, Any]:
        # Requires client_id
        return self._oAuth2Session.fetch_token(
            token_url=self._token_url,
            code=code,
            authorization_response=authorization_response,
            include_client_id=True,
            client_secret=self._client_secret,
        )

    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        sub_scopes: set[str] = set()
        for vertical in verticals:
            if vertical not in self._supported_verticals:
                raise UnsupportedVerticalException([vertical], self._service_name)
            if vertical == Vertical.ExerciseAction:
                sub_scopes.update('activity:read_all', 'profile:read_all')
            elif vertical in [Vertical.FeedPost, Vertical.Follower]:
                sub_scopes.update('activity:read', 'profile:read_all')
            elif vertical == Vertical.Follower:
                sub_scopes.add('profile:read_all')
        return sub_scopes
