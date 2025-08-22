from typing import Any, Iterable, Optional, override

from pardner.exceptions import UnsupportedRequestException, UnsupportedVerticalException
from pardner.services import BaseTransferService
from pardner.services.utils import scope_as_set, scope_as_string
from pardner.verticals import Vertical


class StravaTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Strava's API.
    See API documentation: https://developers.strava.com/docs/reference/
    """

    _authorization_url = 'https://www.strava.com/oauth/authorize'
    _base_url = 'https://www.strava.com/api/v3/'
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
            supported_verticals={Vertical.PhysicalActivity},
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
            if not self.is_vertical_supported(vertical):
                raise UnsupportedVerticalException(
                    vertical, service_name=self._service_name
                )
            if vertical == Vertical.PhysicalActivity:
                sub_scopes.update(['activity:read', 'profile:read_all'])
        return sub_scopes

    def fetch_physical_activities(
        self, request_params: dict[str, Any] = {}, count: int = 30
    ) -> list[Any]:
        """
        Fetches and returns activities completed by the authorized user.

        :param count: number of activities to request. At most 30 at a time.
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        the other arguments to this method.

        :returns: a list of dictionary objects with information for the activities from
        the authorized user.

        :raises: :class:`UnsupportedRequestException` if the request is unable to be
        made.
        """
        max_count = 30
        if count <= max_count:
            return list(
                self._get_resource_from_path(
                    'athlete/activities', params={'per_page': count, **request_params}
                ).json()
            )
        raise UnsupportedRequestException(
            self._service_name,
            f'can only make a request for at most {max_count} activities at a time.',
        )
