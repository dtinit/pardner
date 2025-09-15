import json
from collections import defaultdict
from typing import Any, Iterable, Optional, override
from urllib.parse import parse_qs, urlparse

from oauthlib.oauth2 import MobileApplicationClient
from requests import Response
from requests_oauthlib import OAuth2Session

from pardner.exceptions import UnsupportedRequestException
from pardner.services import BaseTransferService
from pardner.verticals import (
    BlockedUserVertical,
    ChatBotVertical,
    ConversationDirectVertical,
    ConversationGroupVertical,
    Vertical,
)
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


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
    _user_id: str | None = None

    def __init__(
        self, client_id: str, redirect_uri: str, verticals: set[Vertical] = set()
    ) -> None:
        super().__init__(
            service_name='GroupMe',
            client_id=client_id,
            redirect_uri=redirect_uri,
            supported_verticals={
                BlockedUserVertical,
                ChatBotVertical,
                ConversationDirectVertical,
                ConversationGroupVertical,
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

    def fetch_user_data(self, request_params: dict[str, Any] = {}) -> Any:
        """
        Fetches user identifiers and profile data. Also sets ``self._user_id``, which
        is necessary for most requests.

        :returns: user identifiers and profile data in dictionary format.
        """
        user_data = (
            self._get_resource_from_path('users/me', request_params)
            .json()
            .get('response')
        )
        self._user_id = user_data['id']
        return user_data

    def parse_blocked_user_vertical(self, raw_data: Any) -> BlockedUserVertical | None:
        """
        Given the response from the API request, creates a
        :class:`BlockedUserVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`BlockedUserVertical` or ``None``, depending on whether it
        was possible to extract data from the response
        """
        if not isinstance(raw_data, dict):
            return None
        raw_data_dict = defaultdict(dict, raw_data)
        return BlockedUserVertical(
            service=self._service_name,
            creator_user_id=raw_data_dict.get('user_id'),
            data_owner_id=raw_data_dict.get('user_id', self._user_id),
            blocked_user_id=raw_data_dict.get('blocked_user_id'),
            created_at=raw_data_dict.get('created_at'),
        )

    def fetch_blocked_user_vertical(
        self, request_params: dict[str, Any] = {}
    ) -> tuple[list[BlockedUserVertical | None], Any]:
        """
        Sends a GET request to fetch the users blocked by the authenticated user.

        :returns: two elements: the first, a list of :class:`BlockedUserVertical`s
        or ``None``, if unable to parse; the second, the raw response from making the
        request.
        """
        blocked_users = self._fetch_resource_common('blocks', request_params)
        if 'blocks' not in blocked_users:
            raise ValueError(
                f'Unexpected response format: {json.dumps(blocked_users, indent=2)}'
            )
        return [
            self.parse_blocked_user_vertical(blocked_dict)
            for blocked_dict in blocked_users['blocks']
        ], blocked_users

    def parse_chat_bot_vertical(self, raw_data: Any) -> ChatBotVertical | None:
        """
        Given the response from the API request, creates a
        :class:`ChatBotVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`ChatBotVertical` or ``None``, depending on whether it
        was possible to extract data from the response
        """
        if not isinstance(raw_data, dict):
            return None
        raw_data_dict = defaultdict(dict, raw_data)

        user_id = raw_data_dict.get('user_id', self._user_id)

        return ChatBotVertical(
            service=self._service_name,
            service_object_id=raw_data_dict.get('bot_id'),
            creator_user_id=user_id,
            data_owner_id=user_id,
            name=raw_data_dict.get('name'),
            conversation_group_id=raw_data_dict.get('group_id'),
        )

    def fetch_chat_bot_vertical(
        self, request_params: dict[str, Any] = {}
    ) -> tuple[list[ChatBotVertical | None], Any]:
        """
        Sends a GET request to fetch the chat bots created by the authenticated user.

        :returns: two elements: the first, a list of :class:`ChatBotVertical`s
        or ``None``, if unable to parse; the second, the raw response from making the
        request.
        """
        bots_response = self._fetch_resource_common('bots', request_params)
        if not isinstance(bots_response, list):
            raise ValueError(
                f'Unexpected response format: {json.dumps(bots_response, indent=2)}'
            )
        return [
            self.parse_chat_bot_vertical(chat_bot_data)
            for chat_bot_data in bots_response
        ], bots_response

    def parse_conversation_direct_vertical(
        self, raw_data: Any
    ) -> ConversationDirectVertical | None:
        """
        Given the response from the API request, creates a
        :class:`ConversationDirectVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`ConversationDirectVertical` or ``None``, depending on
        whether it was possible to extract data from the response
        """
        if not isinstance(raw_data, dict):
            return None
        raw_data_dict = defaultdict(dict, raw_data)
        return ConversationDirectVertical(
            service=self._service_name,
            service_object_id=raw_data_dict.get('id'),
            data_owner_id=self._user_id,
            member_user_ids=[self._user_id, raw_data_dict['other_user'].get('id')],
            messages_count=raw_data_dict.get('messages_count'),
            created_at=raw_data_dict.get('created_at'),
        )

    def fetch_conversation_direct_vertical(
        self, request_params: dict[str, Any] = {}, count: int = 10
    ) -> tuple[list[ConversationDirectVertical | None], Any]:
        """
        Sends a GET request to fetch the conversations the authenticated user is a part
        of with only one other member (i.e., a direct message). The response will
        include metadata associated with the conversation, but no more than one message
        from the conversation.

        :param count: the number of conversations to fetch. Defaults to 10.

        :returns: two elements: the first, a list of
        :class:`ConversationDirectVertical`s or ``None``, if unable to parse; the
        second, the raw response from making the request.
        """
        if count > 10:
            raise UnsupportedRequestException(
                self._service_name,
                'can only make a request for at most 10 direct conversations at a time.',
            )
        conversation_direct_raw_response = self._fetch_resource_common(
            'chats', params={**request_params, 'per_page': count}
        )
        if not isinstance(conversation_direct_raw_response, list):
            raise ValueError(
                'Unexpected response format. Expected list, '
                f'got: {json.dumps(conversation_direct_raw_response, indent=2)}'
            )
        return [
            self.parse_conversation_direct_vertical(conversation_direct_data)
            for conversation_direct_data in conversation_direct_raw_response
        ], conversation_direct_raw_response

    def parse_conversation_group_vertical(
        self, raw_data: Any
    ) -> ConversationGroupVertical | None:
        """
        Given the response from the API request, creates a
        :class:`ConversationGroupVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`ConversationGroupVertical` or ``None``, depending on
        whether it was possible to extract data from the response
        """
        if not isinstance(raw_data, dict):
            return None
        raw_data_dict = defaultdict(dict, raw_data)

        members_list = raw_data_dict.get('members', [])
        member_user_ids = []
        for member in members_list:
            if isinstance(member, dict) and 'user_id' in member:
                member_user_ids.append(member['user_id'])

        associated_media = []
        image_url = raw_data_dict.get('image_url', None)
        if image_url:
            associated_media = [AssociatedMediaSubVertical(image_url=image_url)]

        is_private = None
        conversation_type = raw_data_dict.get('type')
        if isinstance(conversation_type, str):
            is_private = conversation_type == 'private'

        return ConversationGroupVertical(
            service=self._service_name,
            service_object_id=raw_data_dict.get('id'),
            data_owner_id=self._user_id,
            creator_user_id=raw_data_dict.get('creator_user_id'),
            title=raw_data_dict.get('name'),
            member_user_ids=member_user_ids,
            members_count=len(members_list),
            messages_count=raw_data_dict['messages'].get('count'),
            associated_media=associated_media,
            created_at=raw_data_dict.get('created_at'),
            is_private=is_private,
        )

    def fetch_conversation_group_vertical(
        self, request_params: dict[str, Any] = {}, count: int = 10
    ) -> Any:
        """
        Sends a GET request to fetch the group conversations the authenticated user is
        a part of. The response will include metadata associated with the conversation,
        but no more than one message from the conversation.

        :param count: the number of conversations to fetch. Defaults to 10.

        :returns: two elements: the first, a list of
        :class:`ConversationGroupVertical`s or ``None``, if unable to parse; the
        second, the raw response from making the request.
        """
        if count > 10:
            raise UnsupportedRequestException(
                self._service_name,
                'can only make a request for at most 10 group conversations at a time.',
            )
        conversation_group_raw_response = self._fetch_resource_common(
            'groups', params={**request_params, 'per_page': count}
        )
        if not isinstance(conversation_group_raw_response, list):
            raise ValueError(
                'Unexpected response format. Expected list, '
                f'got: {json.dumps(conversation_group_raw_response, indent=2)}'
            )
        return [
            self.parse_conversation_group_vertical(conversation_group_data)
            for conversation_group_data in conversation_group_raw_response
        ], conversation_group_raw_response
