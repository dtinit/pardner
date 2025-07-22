from typing import Any, Iterable, Optional

from pardner.services import BaseTransferService
from pardner.verticals import Vertical


class TumblrTransferService(BaseTransferService):
    _authorization_url = 'https://www.tumblr.com/oauth2/authorize'
    _token_url = 'https://api.tumblr.com/v2/oauth2/token'

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        verticals: set[Vertical] = set(),
    ) -> None:
        super().__init__(
            service_name='Tumblr',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            supported_verticals={Vertical.FeedPost},
            verticals=verticals,
        )

    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        # Tumblr only needs 'base' for read access requests
        return {'base'}

    def authorization_url(self) -> tuple[str, str]:
        return self._oAuth2Session.authorization_url(self._authorization_url)

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
