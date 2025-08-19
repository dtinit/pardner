import json
from typing import Any, Iterable, Optional, override
from urllib.parse import parse_qs, urlparse

from oauthlib.oauth2 import MobileApplicationClient
from requests import Response
from requests_oauthlib import OAuth2Session

from pardner.services.base import BaseTransferService, UnsupportedRequestException
from pardner.verticals import Vertical


class GroupMeTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to GroupMe's
    API.
    See API documentation: https://dev.groupme.com/docs/v3

    Note that GroupMe authorizes user access via the implicit OAuth flow as of August
    2025. This means the access token is obtained after the first request to GroupMe's
    servers. This is less secure than the traditional OAuth 2.0 flow.
    """

    _authorization_url = 'https://oauth.groupme.com/oauth/authorize'
    _base_url = 'https://api.groupme.com/v3/'
    _token_url = 'https://oauth.groupme.com/oauth/authorize'
    _user_id: str | None

    def __init__(
        self, client_id: str, redirect_uri: str, verticals: set[Vertical] = set()
    ) -> None:
        super().__init__(
            service_name='GroupMe',
            client_id=client_id,
            redirect_uri=redirect_uri,
            supported_verticals={
                Vertical.BlockedUser,
                Vertical.ChatBot,
                Vertical.ConversationDirect,
                Vertical.ConversationGroup,
            },
            verticals=verticals,
        )
        implicit_grant_application_client = MobileApplicationClient(client_id=client_id)
        self._oAuth2Session = OAuth2Session(
            client=implicit_grant_application_client, redirect_uri=redirect_uri
        )

    @override
    def _get_resource_from_path(
        self, path_suffix: str, params: dict[str, Any] = {}
    ) -> Response:
        access_token = self._oAuth2Session.token.get('access_token')
        if not access_token:
            raise UnsupportedRequestException(
                self._service_name,
                'Must send token as a parameter for GET requests. Use fetch_token(...) '
                'to automatically fetch and send the token.',
            )
        return super()._get_resource_from_path(
            path_suffix, params={'token': access_token, **params}
        )

    def _fetch_resource_common(
        self, path_suffix: str, params: dict[str, Any] = {}
    ) -> Any:
        """
        Helper method for fetching data that follows a common format with common
        parameters.

        :param path_suffix: the part of the path that identifies a GroupMe API endpoint.
        :param params: an optional dictionary of parameters to pass with the GET request
        to GroupMe's API.

        :returns: a JSON object with the result of the request.
        """
        if not self._user_id:
            self.fetch_user_data()

        return (
            self._get_resource_from_path(
                path_suffix, params={'user': self._user_id, **params}
            )
            .json()
            .get('response')
        )

    @override
    def fetch_token(
        self,
        code: Optional[str] = None,
        authorization_response: Optional[str] = None,
        include_client_id: bool = True,
    ) -> dict[str, Any]:
        if not authorization_response:
            raise ValueError(
                'GroupMe requires an authorization response URL instead of code.'
            )
        url_query = urlparse(authorization_response).query
        url_query_params = parse_qs(url_query)

        access_token_list = url_query_params.get('access_token')
        if not access_token_list:
            raise ValueError(
                f'Could not fetch access token using the {authorization_response}.'
            )

        self._oAuth2Session.token['access_token'] = access_token_list[0]
        return self._oAuth2Session.token if self._oAuth2Session.token else {}

    @override
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        # GroupMe does not require scope
        return set()

    def fetch_user_data(self) -> Any:
        """
        Fetches user identifiers and profile data. Also sets ``self._user_id``, which
        is necessary for most requests.

        :returns: user identifiers and profile data in dictionary format.
        """
        user_data = self._get_resource_from_path('users/me').json().get('response')
        self._user_id = user_data['id']
        return user_data

    def fetch_blocked_users(self) -> Any:
        """
        Sends a GET request to fetch the users blocked by the authenticated user.

        :returns: a JSON object with the result of the request.
        """
        blocked_users = self._fetch_resource_common('blocks')

        if 'blocks' not in blocked_users:
            raise ValueError(
                f'Unexpected response format: {json.dumps(blocked_users, indent=2)}'
            )

        return blocked_users['blocks']

    def fetch_chat_bots(self) -> Any:
        """
        Sends a GET request to fetch the chat bots created by the authenticated user.

        :returns: a JSON object with the result of the request.
        """
        return self._fetch_resource_common('bots')

    def fetch_conversations_direct(self, count: int = 10) -> Any:
        """
        Sends a GET request to fetch the conversations the authenticated user is a part
        of with only one other member (i.e., a direct message). The response will
        include metadata associated with the conversation and messages from the
        conversation.

        :param count: the number of messages to fetch. Defaults to 10.

        :returns: a JSON object with the result of the request.
        """
        if count <= 10:
            return self._fetch_resource_common('chats', params={'per_page': count})
        raise UnsupportedRequestException(
            self._service_name,
            'can only make a request for at most 10 direct conversations at a time.',
        )

    def fetch_conversations_group(self, count: int = 10) -> Any:
        """
        Sends a GET request to fetch the group conversations the authenticated user is
        a part of. The response will include metadata associated with the conversation
        and messages from the conversation.

        :param count: the number of messages to fetch. Defaults to 10.

        :returns: a JSON object with the result of the request.
        """
        if count <= 10:
            return self._fetch_resource_common('groups', params={'per_page': count})
        raise UnsupportedRequestException(
            self._service_name,
            'can only make a request for at most 10 group conversations at a time.',
        )
