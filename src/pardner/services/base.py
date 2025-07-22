from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

from requests_oauthlib import OAuth2Session

from pardner.verticals import Vertical


class InsufficientScopeException(Exception):
    def __init__(
        self, unsupported_verticals: Iterable[Vertical], service_name: str
    ) -> None:
        combined_verticals = ' '.join(unsupported_verticals)
        super().__init__(
            f'Cannot add {combined_verticals} to {service_name} with current scope.'
        )


class UnsupportedVerticalException(Exception):
    def __init__(
        self, unsupported_verticals: Iterable[Vertical], service_name: str
    ) -> None:
        combined_verticals = ' '.join(unsupported_verticals)
        super().__init__(
            f'Cannot add {combined_verticals} to {service_name} because they are not supported.'
        )


class BaseTransferService(ABC):
    """
    A base class to be extended by service-specific classes that implement logic for
    OAuth 2.0 and data transfers.
    """

    _client_secret: str
    _oAuth2Session: OAuth2Session
    _service_name: str
    _supported_verticals: set[Vertical] = set()
    _verticals: set[Vertical] = set()

    def __init__(
        self,
        service_name: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        supported_verticals: set[Vertical],
        verticals: set[Vertical] = set(),
    ) -> None:
        """
        Initializes an instance of BaseTransferService, which shouldn't be done unless
        by classes that extend it.

        :param service_name: Name of the service for which the transfer is being built.
        :param client_id: Client identifier given by the OAuth provider upon registration.
        :param client_secret: The `client_secret` paired to the `client_id`.
        :param redirect_uri: The registered callback URI.
        :param supported_verticals: The `Vertical`s that can be fetched on the service.
        :param verticals: The `Vertical`s for which the transfer service has
        appropriate scope to fetch.
        """
        self._oAuth2Session = OAuth2Session(
            client_id=client_id, redirect_uri=redirect_uri
        )
        self._client_secret = client_secret
        self._supported_verticals = supported_verticals
        self._service_name = service_name
        self._verticals = verticals

    @property
    def name(self) -> str:
        return self._service_name

    @property
    def scope(self) -> set[str]:
        return self._oAuth2Session.scope if self._oAuth2Session.scope else set()

    @scope.setter
    def scope(self, new_scope: Iterable[str]) -> None:
        self._oAuth2Session.scope = set(new_scope)

    @property
    def verticals(self) -> set[Vertical]:
        return self._verticals

    @verticals.setter
    def verticals(self, verticals: Iterable[Vertical]) -> None:
        """
        :raises: :class:`UnsupportedVerticalException`: if one or more of the
        `verticals` are not supported by the service.
        """
        unsupported_verticals = [
            vertical
            for vertical in verticals
            if vertical not in self._supported_verticals
        ]
        if len(unsupported_verticals) > 0:
            raise UnsupportedVerticalException(unsupported_verticals, self.name)
        self._verticals = set(verticals)

    def add_verticals(
        self, verticals: Iterable[Vertical], should_reauth: bool = False
    ) -> bool:
        """
        Adds to the verticals being requested.

        :param verticals: `Vertical`s that should be added to service.
        :param should_reauth: Whether or not the service should unauthorize itself to
        start a new session with added scopes corresponding to `verticals`.

        :returns: Whether add was successful without reauthorization (`True`) or not
        (`False`).

        :raises: :class:`UnsupportedVerticalException`: if `should_reauth` is not
        passed and the current scopes are insufficient, this exception is raised.
        """
        new_verticals = set(verticals) - self.verticals
        new_scopes = self.scope_for_verticals(new_verticals)
        original_scopes: set[str] = self.scope if self.scope else set()

        if not new_scopes.issubset(original_scopes) and not should_reauth:
            raise InsufficientScopeException(verticals, self.name)
        elif not new_scopes.issubset(original_scopes):
            self.verticals = new_verticals | self.verticals
            del self._oAuth2Session.access_token
            self.scope = original_scopes | new_scopes
            return False

        self.verticals = new_verticals | self.verticals
        return True

    @abstractmethod
    def fetch_token(
        self, code: Optional[str] = None, authorization_response: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Once the end-user authorizes the application to access their data, the
        resource server sends a request to `redirect_uri` with the authorization code as
        a parameter. Using this authorization code, this method makes a request to the
        resource server to obtain the access token.

        One of either `code` or `authorization_response` must not be None.

        :param code: the code obtained from parsing the callback URL which the end-user's
        browser redirected to.
        :param authorization_response: the URL (with parameters) the end-user's browser
        redirected to after authorization.

        :returns: the authorization URL and state, respectively.
        """
        pass

    @abstractmethod
    def authorization_url(self) -> tuple[str, str]:
        """
        Builds the authorization URL and state. Once the end-user (i.e., resource owner)
        navigates to the authorization URL they can begin the authorization flow.

        :returns: the authorization URL and state, respectively.
        """
        pass

    @abstractmethod
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        """
        Given a vertical, returns the scopes necessary for making API requests for
        fetching data in that vertical.

        :param verticals: The verticals for which scopes are being requested.

        :returns: Scope names corresponding to `verticals`.
        """
        pass
