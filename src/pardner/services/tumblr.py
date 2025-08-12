from typing import Any, Iterable, Optional, override

from pardner.services import BaseTransferService
from pardner.verticals import Vertical


class TumblrTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Tumblr's API.
    See API documentation: https://www.tumblr.com/docs/en/api/v2
    """

    _authorization_url = 'https://www.tumblr.com/oauth2/authorize'
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
