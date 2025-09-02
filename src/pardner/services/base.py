from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional
from urllib.parse import urljoin

from requests import Response
from requests_oauthlib import OAuth2Session

from pardner.exceptions import InsufficientScopeException, UnsupportedVerticalException
from pardner.services.utils import scope_as_set, scope_as_string
from pardner.verticals import Vertical


class BaseTransferService(ABC):
    """
    A base class to be extended by service-specific classes that implement logic for
    OAuth 2.0 and data transfers.
    """

    _authorization_url: str
    _base_url: str
    _client_secret: str | None
    _oAuth2Session: OAuth2Session
    _service_name: str
    _supported_verticals: set[Vertical] = set()
    _token_url: str
    _verticals: set[Vertical] = set()

    def __init__(
        self,
        service_name: str,
        client_id: str,
        redirect_uri: str,
        supported_verticals: set[Vertical],
        client_secret: Optional[str] = None,
        state: Optional[str] = None,
        verticals: set[Vertical] = set(),
    ) -> None:
        """
        Initializes an instance of BaseTransferService, which shouldn't be done unless
        by classes that extend it.

        :param service_name: Name of the service for which the transfer is being built.
        :param client_id: Client identifier given by the OAuth provider upon registration.
        :param redirect_uri: The registered callback URI.
        :param supported_verticals: The :class:`Vertical`s that can be fetched on the service.
        :param client_secret: The ``client_secret`` paired to the ``client_id``.
        :param state: State string used to prevent CSRF and identify flow.
        :param verticals: The :class:`Vertical`s for which the transfer service has
        appropriate scope to fetch.
        """
        self._client_secret = client_secret
        self._supported_verticals = supported_verticals
        self._service_name = service_name
        self._verticals = verticals
        self._oAuth2Session = OAuth2Session(
            client_id=client_id, redirect_uri=redirect_uri, state=state
        )
        self.scope = self.scope_for_verticals(verticals)

    @property
    def name(self) -> str:
        return self._service_name

    @property
    def scope(self) -> set[str]:
        return (
            scope_as_set(self._oAuth2Session.scope)
            if self._oAuth2Session.scope
            else set()
        )

    @scope.setter
    def scope(self, new_scope: Iterable[str]) -> None:
        """
        Sets the scope of the transfer service flow.
        Some services have specific requirements for the format of the scope
        string (e.g., scopes have to be comma separated, or ``+`` separated).

        :param new_scope: The new scopes that should be set for the transfer
        service.
        """
        self._oAuth2Session.scope = scope_as_string(new_scope)

    @property
    def verticals(self) -> set[Vertical]:
        return self._verticals

    @verticals.setter
    def verticals(self, verticals: Iterable[Vertical]) -> None:
        """
        :raises: :class:`UnsupportedVerticalException`: if one or more of the
        ``verticals`` are not supported by the service.
        """
        unsupported_verticals = [
            vertical
            for vertical in verticals
            if not self.is_vertical_supported(vertical)
        ]
        if len(unsupported_verticals) > 0:
            raise UnsupportedVerticalException(
                *unsupported_verticals, service_name=self.name
            )
        self._verticals = set(verticals)

    def _get_resource(self, uri: str, params: dict[str, Any] = {}) -> Response:
        """
        Sends a GET request to ``uri`` using :class:`OAuth2Session`.

        :param uri: the destination of the request (a URI).
        :param params: the extra parameters to be send with the request, optionally.

        :returns: The :class:`requests.Response` object obtained from making the request.
        """
        response = self._oAuth2Session.get(uri, params=params)
        if not response.ok:
            response.raise_for_status()
        return response

    def _build_resource_url(self, path_suffix: str, base: Optional[str] = None) -> str:
        """
        Constructs the resource URL from a domain and path suffix.

        :param path_suffix: the path to append to ``base``.
        :param base: the prefix of the resource URL. If not given, defaults to
        ``self._base_url``.

        :returns: the complete resource URL.
        """
        if not base:
            base = self._base_url
        if not base.endswith('/'):
            base += '/'

        if path_suffix.startswith('/'):
            path_suffix = path_suffix[1:]

        return urljoin(base, path_suffix)

    def _get_resource_from_path(
        self, path_suffix: str, params: dict[str, Any] = {}
    ) -> Response:
        """
        Sends a GET request to the endpoint URL built using ``endpoint_path``.

        :param path_suffix: the path of the endpoint being accessed.
        :param params: the extra parameters to be send with the request, optionally.

        :returns: The :class:`requests.Response` object obtained from making the request.
        """
        resource_url = self._build_resource_url(path_suffix)
        return self._get_resource(resource_url, params)

    def add_verticals(
        self, verticals: Iterable[Vertical], should_reauth: bool = False
    ) -> bool:
        """
        Adds to the verticals being requested.

        :param verticals: :class:`Vertical`s that should be added to service.
        :param should_reauth: Whether or not the service should unauthorize itself to
        start a new session with added scopes corresponding to ``verticals``.

        :returns: Whether add was successful without reauthorization (``True``) or not
        (``False``).

        :raises: :class:`UnsupportedVerticalException`: if ``should_reauth`` is not
        passed and the current scopes are insufficient, this exception is raised.
        """
        new_verticals = set(verticals) - self.verticals
        new_scopes = self.scope_for_verticals(new_verticals)

        if not new_scopes.issubset(self.scope) and not should_reauth:
            raise InsufficientScopeException(*verticals, service_name=self.name)
        elif not new_scopes.issubset(self.scope):
            self.verticals = new_verticals | self.verticals
            del self._oAuth2Session.access_token
            self.scope = self.scope | new_scopes
            return False

        self.verticals = new_verticals | self.verticals
        return True

    def is_vertical_supported(self, vertical: Vertical) -> bool:
        """
        Utility for indicating whether ``vertical`` is supported by the service or not.

        :param vertical: the ``vertical`` from which validity is checked.

        :returns: ``True`` if supported, ``False`` otherwise.
        """
        return vertical in self._supported_verticals

    def fetch_token(
        self,
        code: Optional[str] = None,
        authorization_response: Optional[str] = None,
        include_client_id: bool = False,
    ) -> dict[str, Any]:
        """
        Once the end-user authorizes the application to access their data, the
        resource server sends a request to ``redirect_uri`` with the authorization code as
        a parameter. Using this authorization code, this method makes a request to the
        resource server to obtain the access token.

        One of either ``code`` or ``authorization_response`` must not be None.

        :param code: the code obtained from parsing the callback URL which the end-user's
        browser redirected to.
        :param authorization_response: the URL (with parameters) the end-user's browser
        redirected to after authorization.
        :param include_client_id: whether or not to send the client ID with the token request

        :returns: the authorization URL and state, respectively.
        """
        return self._oAuth2Session.fetch_token(
            token_url=self._token_url,
            code=code,
            authorization_response=authorization_response,
            include_client_id=include_client_id,
            client_secret=self._client_secret,
        )

    def authorization_url(self) -> tuple[str, str]:
        """
        Builds the authorization URL and state. Once the end-user (i.e., resource owner)
        navigates to the authorization URL they can begin the authorization flow.

        :returns: the authorization URL and state, respectively.
        """
        return self._oAuth2Session.authorization_url(self._authorization_url)

    @abstractmethod
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        """
        Given a vertical, returns the scopes necessary for making API requests for
        fetching data in that vertical.

        :param verticals: The verticals for which scopes are being requested.

        :returns: Scope names corresponding to ``verticals``.
        """
        pass

    def fetch(
        self, vertical: Vertical, request_params: dict[str, Any] = {}, **params: Any
    ) -> Any:
        """
        Generic method for fetching data of a specific vertical.

        :param vertical: the :class:`Vertical` to fetch from the
        service.
        :param request_params: additional request parameters to be sent with the HTTP
        request. Requires familiarity with the API of the service being used.
        :param params: optional keyword arguments to be passed to the methods for
        fetching ``vertical``.

        :returns: the JSON response resulting from making the request.

        :raises: :class:`UnsupportedVerticalException` if the vertical is not supported.
        """
        if not self.is_vertical_supported(vertical):
            raise UnsupportedVerticalException(
                vertical, service_name=self._service_name
            )

        method_name = f'fetch_{vertical.vertical_name}_vertical'
        getattr(self, method_name)(request_params=request_params, **params)
