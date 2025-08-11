from typing import Any, Iterable, Optional, override

from pardner.services.base import BaseTransferService, UnsupportedVerticalException
from pardner.services.utils import scope_as_set, scope_as_string
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
        state: Optional[str] = None,
        verticals: set[Vertical] = set(),
    ) -> None:
        super().__init__(
            service_name='Strava',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            state=state,
            supported_verticals={Vertical.FeedPost},
            verticals=verticals,
        )

    @property
    def scope(self) -> set[str]:
        return scope_as_set(self._oAuth2Session.scope, delimiter=',')

    @scope.setter
    def scope(self, new_scope: Iterable[str] | str) -> None:
        self._oAuth2Session.scope = scope_as_string(new_scope, delimiter=',')

    @override
    def fetch_token(
        self,
        code: Optional[str] = None,
        authorization_response: Optional[str] = None,
        include_client_id: bool = True,
    ) -> dict[str, Any]:
        return super().fetch_token(code, authorization_response, include_client_id)

    @override
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        sub_scopes: set[str] = set()
        for vertical in verticals:
            if vertical not in self._supported_verticals:
                raise UnsupportedVerticalException([vertical], self._service_name)
            if vertical == Vertical.FeedPost:
                sub_scopes.update(['activity:read', 'profile:read_all'])
        return sub_scopes
