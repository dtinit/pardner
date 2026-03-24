import json
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Optional, override

from requests import HTTPError

from pardner.exceptions import TumblrAPIError, UnsupportedRequestException
from pardner.services import BaseTransferService
from pardner.verticals import SocialPostingVertical, Vertical
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


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
    
    def _validate_user_info_response(self, data: Any) -> dict[str, Any]:
        """
        Validates the shape of a ``user/info`` JSON payload.

        :param data: the parsed JSON dict returned by ``user/info``.
        :returns: the ``response`` sub-dict if validation passes.
        :raises: :class:`TumblrAPIError` if required keys are absent or have the wrong type.
        """
        if not isinstance(data, dict):
            raise TumblrAPIError(
                'user/info response is not a JSON object', raw_response=data
            )
        response = data.get('response')
        if not isinstance(response, dict):
            raise TumblrAPIError(
                "user/info response is missing a 'response' object", raw_response=data
            )
        user = response.get('user')
        if not isinstance(user, dict):
            raise TumblrAPIError(
                'user/info response.user is missing or not an object', raw_response=data
            )
        blogs = user.get('blogs')
        if not isinstance(blogs, list):
            raise TumblrAPIError(
                'user/info response.user.blogs is missing or not a list',
                raw_response=data,
            )
        return response

    def _validate_dashboard_response(self, data: Any) -> list[Any]:
        """
        Validates the shape of a ``user/dashboard`` JSON payload.

        :param data: the parsed JSON dict returned by ``user/dashboard``.
        :returns: the ``posts`` list if validation passes.
        :raises: :class:`TumblrAPIError` if required keys are absent or have the wrong type.
        """
        if not isinstance(data, dict):
            raise TumblrAPIError(
                'user/dashboard response is not a JSON object', raw_response=data
            )
        response = data.get('response')
        if not isinstance(response, dict):
            raise TumblrAPIError(
                "user/dashboard response is missing a 'response' object",
                raw_response=data,
            )
        posts = response.get('posts')
        if not isinstance(posts, list):
            raise TumblrAPIError(
                'user/dashboard response.posts is missing or not a list',
                raw_response=data,
            )
        return posts

    def _map_tumblr_state(
        self, state: str | None
    ) -> Literal['public', 'private', 'draft', 'restricted'] | None:
        """Maps a Tumblr post ``state`` string to the vertical status literal."""
        mapping: dict[str, Literal['public', 'private', 'draft', 'restricted']] = {
            'published': 'public',
            'private': 'private',
            'draft': 'draft',
            'queued': 'restricted',
            'queue': 'restricted',
        }
        return mapping.get(state or '', None)

    def parse_social_posting_vertical(
        self, raw_data: Any
    ) -> SocialPostingVertical | None:
        """
        Given a single raw Tumblr post dict, creates a
        :class:`SocialPostingVertical` model object, if possible.

        Maps stable NPF fields: ``id``, ``post_url``, ``timestamp``,
        ``summary``, ``note_count``, ``tags``, ``state``, NPF content
        text blocks, and media blocks.

        :param raw_data: a single post dict from the Tumblr dashboard response.
        :returns: :class:`SocialPostingVertical` or ``None`` if ``raw_data``
        is not a dict.
        """
        if not isinstance(raw_data, dict):
            return None

        # identity / location
        service_object_id: str | None = str(raw_data['id']) if 'id' in raw_data else None
        post_url: str | None = raw_data.get('post_url') or raw_data.get('short_url')

        created_at: datetime | None = None
        timestamp = raw_data.get('timestamp')
        if isinstance(timestamp, (int, float)):
            created_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(
                tzinfo=None
            )

        blog = raw_data.get('blog') or {}
        creator_user_id: str | None = (
            blog.get('uuid') or blog.get('name') or raw_data.get('blog_name')
        )
        data_owner_id: str = self.primary_blog_id or ''

        interaction_count: int | None = raw_data.get('note_count')
        keywords: list[str] = raw_data.get('tags') or []

        status = self._map_tumblr_state(raw_data.get('state'))

        # NPF content blocks
        content_blocks: list[dict[str, Any]] = raw_data.get('content') or []
        text_parts: list[str] = []
        associated_media: list[AssociatedMediaSubVertical] = []

        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get('type', '')
            if block_type == 'text':
                text_value = block.get('text')
                if isinstance(text_value, str) and text_value:
                    text_parts.append(text_value)
            elif block_type in ('image', 'video', 'audio'):
                media_type_map: dict[str, Literal['audio', 'image', 'video']] = {
                    'image': 'image',
                    'video': 'video',
                    'audio': 'audio',
                }
                media_type = media_type_map.get(block_type)
                media_entries: list[dict[str, Any]] = block.get('media') or []
                if isinstance(media_entries, list):
                    for entry in media_entries:
                        if isinstance(entry, dict) and entry.get('url'):
                            associated_media.append(
                                AssociatedMediaSubVertical(
                                    media_type=media_type, url=entry['url']
                                )
                            )
                elif isinstance(media_entries, dict) and media_entries.get('url'):
                    associated_media.append(
                        AssociatedMediaSubVertical(
                            media_type=media_type, url=media_entries['url']
                        )
                    )

        return SocialPostingVertical(
            creator_user_id=creator_user_id,
            data_owner_id=data_owner_id,
            service_object_id=service_object_id,
            service=self._service_name,
            created_at=created_at,
            url=post_url,
            abstract=raw_data.get('summary'),
            interaction_count=interaction_count,
            keywords=keywords,
            status=status,
            text='\n\n'.join(text_parts) if text_parts else None,
            associated_media=associated_media,
        )

    def fetch_primary_blog_id(self) -> str:
        """
        Fetches the primary blog ID from the data owner, which will be used as the
        ``data_owner_id`` in the vertical model objects. If the ``primary_blog_id``
        attribute on this class is already set, the method does not make a new request.

        Note: "PrimaryBlogId" is not a vertical. This is used purely as a unique
        identifier for the user, since Tumblr doesn't provide one by default.

        :returns: the primary blog id.

        :raises: :class:`TumblrAPIError`: if the Tumblr API returns a non-OK response
        or a malformed success payload.
        :raises: :class:`ValueError`: if the response is structurally valid but no
        primary blog with a UUID was found.
        """
        if self.primary_blog_id:
            return self.primary_blog_id

        try:
            raw_response = self._get_resource_from_path('user/info')
        except HTTPError as exc:
            raise TumblrAPIError(
                'Failed to fetch user/info',
                status_code=exc.response.status_code if exc.response is not None else None,
                raw_response=exc.response,
            ) from exc

        user_info_data = raw_response.json()
        response = self._validate_user_info_response(user_info_data)

        for blog_info in response['user']['blogs']:
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
            f'{json.dumps(user_info_data, indent=2)}'
        )

    def fetch_social_posting_vertical(
        self,
        request_params: dict[str, Any] = {},
        count: int = 20,
        text_only: bool = True,
    ) -> tuple[list[SocialPostingVertical | None], list[Any]]:
        """
        Fetches posts from Tumblr feed for the user account whose token was
        obtained using the Tumblr API.

        :param count: number of posts to request.
        :param text_only: whether or not to request only text-based posts (``True``) or
        not (``False``).
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        ``count`` and ``text_only``.

        :returns: a two-element tuple: the first element is a list of
        :class:`SocialPostingVertical` objects (``None`` for posts that could
        not be parsed); the second element is the raw list of post dicts as
        returned by the API.

        :raises: :class:`UnsupportedRequestException` if ``count`` exceeds 20.
        :raises: :class:`TumblrAPIError` if the API returns a non-OK response
        or a malformed success payload.
        """
        if count > 20:
            raise UnsupportedRequestException(
                self._service_name,
                'can only make a request for at most 20 posts at a time.',
            )

        params: dict[str, Any] = {'limit': count, 'npf': True, **request_params}
        if text_only:
            params['type'] = 'text'

        try:
            dashboard_response = self._get_resource_from_path('user/dashboard', params)
        except HTTPError as exc:
            raise TumblrAPIError(
                'Failed to fetch user/dashboard',
                status_code=exc.response.status_code if exc.response is not None else None,
                raw_response=exc.response,
            ) from exc

        raw_posts = self._validate_dashboard_response(dashboard_response.json())
        parsed = [self.parse_social_posting_vertical(post) for post in raw_posts]
        return parsed, raw_posts
