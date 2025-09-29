import json
from typing import Any, Iterable, Optional, override

from pardner.exceptions import UnsupportedRequestException
from pardner.services import BaseTransferService
from pardner.verticals import SocialPostingVertical, Vertical


class TumblrTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Tumblr's API.
    See API documentation: https://www.tumblr.com/docs/en/api/v2
    """

    primary_blog_id: str | None = None
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
        primary_blog_id: str | None = None,
    ) -> None:
        """
        Creates an instance of ``TumblrTransferService``.

        :param client_id: Client identifier given by the OAuth provider upon registration.
        :param client_secret: The ``client_secret`` paired to the ``client_id``.
        :param redirect_uri: The registered callback URI.
        :param state: State string used to prevent CSRF and identify flow.
        :param verticals: The :class:`Vertical`s for which the transfer service has
        appropriate scope to fetch.
        :param primary_blog_id: Optionally, the primary blog ID of the data owner (the
        user being authorized).
        """
        super().__init__(
            service_name='Tumblr',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            state=state,
            supported_verticals={SocialPostingVertical},
            verticals=verticals,
        )
        self.primary_blog_id = primary_blog_id

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

    def fetch_primary_blog_id(self) -> str:
        """
        Fetches the primary blog ID from the data owner, which will be used as the
        ``data_owner_id`` in the vertical model objects. If the ``primary_blog_id``
        attribute on this class is already set, the method does not make a new request.

        Note: "PrimaryBlogId" is not a vertical. This is used purely as a unique
        identifier for the user, since Tumblr doesn't provide one by default.

        :returns: the primary blog id.

        :raises: :class:`ValueError`: if the primary blog ID could not be extracted from
        the response.
        """
        if self.primary_blog_id:
            return self.primary_blog_id
        user_info = self._get_resource_from_path('user/info').json().get('response', {})
        for blog_info in user_info.get('user', {}).get('blogs', []):
            if (
                isinstance(blog_info, dict)
                and blog_info.get('primary')
                and 'uuid' in blog_info
                and isinstance(blog_info['uuid'], str)
            ):
                self.primary_blog_id = blog_info['uuid']
                return blog_info['uuid']

        raise ValueError(
            'Failed to fetch primary blog id. Either manually set the _primary_blog_id '
            'attribute or verify all the client credentials '
            'and permissions are correct. Response from Tumblr: '
            f'{json.dumps(user_info, indent=2)}'
        )

    def fetch_social_posting_vertical(
        self,
        request_params: dict[str, Any] = {},
        count: int = 20,
        text_only: bool = True,
    ) -> list[Any]:
        """
        Fetches posts from Tumblr feed for user account whose token was
        obtained using the Tumblr API.

        :param count: number of posts to request.
        :param text_only: whether or not to request only text-based posts (``True``) or
        not (``False``).
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        ``count`` and ``text_only``.

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
