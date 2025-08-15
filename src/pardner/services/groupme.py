from typing import Any, Iterable, Optional, override

from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

from pardner.services.base import BaseTransferService
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

    _base_url = 'https://api.groupme.com/'
    _token_url = 'https://oauth.groupme.com/oauth/authorize'
    _user_id: str | None

    def __init__(self, client_id: str, redirect_uri: str) -> None:
        super().__init__(
            service_name='GroupMe',
            client_id=client_id,
            redirect_uri=redirect_uri,
            supported_verticals={
                Vertical.BlockedUser,
                Vertical.ChatBot,
                Vertical.Conversation,
                Vertical.ConversationMember,
                Vertical.ConversationMessage,
            },
        )
        implicit_grant_application_client = MobileApplicationClient(client_id=client_id)
        self._oAuth2Session = OAuth2Session(
            client=implicit_grant_application_client, redirect_uri=redirect_uri
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
        return self._oAuth2Session.token_from_fragment(authorization_response)

    @override
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        # GroupMe does not require scope
        return set()

    def fetch_user_data(self) -> dict:
        """
        Fetches user data
        """
        user_data_url = self._build_resource_url('users/me')
        user_data = self._get_resource(user_data_url).json()

        self._user_id = user_data['id']

        if type(user_data) != dict[str, Any]:
            return user_data

    def fetch_blocked_users(self) -> list[Any]:
        blocked_users_uri = self._build_resource_url('blocks')

        return []
