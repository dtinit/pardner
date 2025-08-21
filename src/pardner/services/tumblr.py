from typing import Any, Iterable, Optional, override

from pardner.exceptions import UnsupportedRequestException
from pardner.services import BaseTransferService
from pardner.verticals import Vertical


class TumblrTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Tumblr's API.
    See API documentation: https://www.tumblr.com/docs/en/api/v2
    """

    _authorization_url = 'https://www.tumblr.com/oauth2/authorize'
    _base_url = 'https://api.tumblr.com/v2/'
    _token_url = 'https://api.tumblr.com/v2/oauth2/token'

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        state: Optional[str] = None,
        verticals: set[Vertical] = set(),
    ) -> None:
        super().__init__(
            service_name='Tumblr',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            state=state,
            supported_verticals={Vertical.FeedPost},
            verticals=verticals,
        )

    @override
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        # Tumblr only needs 'basic' for read access requests
        return {'basic'}

    @override
    def fetch_token(
        self,
        code: Optional[str] = None,
        authorization_response: Optional[str] = None,
        include_client_id: bool = True,
    ) -> dict[str, Any]:
        return super().fetch_token(code, authorization_response, include_client_id)

    def fetch_feed_posts(
        self,
        request_params: dict[str, Any] = {},
        count: int = 20,
        text_only: bool = True,
    ) -> list[Any]:
        """
        Fetches posts from Tumblr feed for user account whose token was
        obtained using the Tumblr API.

        :param count: number of posts to request.
        :param text_only: whether or not to request only text-based posts (`True`) or
        not (`False).
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        `count` and `text_only`.

        :returns: a list of dictionary objects with information for the posts in a feed.

        :raises: :class:`UnsupportedRequestException` if the request is unable to be
        made.
        """
        if count <= 20:
            dashboard_response = self._get_resource_from_path(
                'user/dashboard',
                {
                    'limit': count,
                    'npf': True,
                    'type': 'text' if text_only else '',
                    **request_params,
                },
            )
            return list(dashboard_response.json().get('response').get('posts'))
        raise UnsupportedRequestException(
            self._service_name,
            'can only make a request for at most 20 posts at a time.',
        )
