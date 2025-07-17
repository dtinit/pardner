from abc import ABC, abstractmethod
from typing import Iterable

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from pardner.verticals.base import Vertical


class InsufficientScopeException(Exception):
    def __init__(self, unsupported_verticals: Iterable[Vertical], service_name: str):
        combined_verticals = ' '.join(unsupported_verticals)
        super().__init__(f'Cannot add {combined_verticals} to {service_name} with current scope.')


class UnsupportedVerticalException(Exception):
    def __init__(self, unsupported_verticals: Iterable[Vertical], service_name: str):
        combined_verticals = ' '.join(unsupported_verticals)
        super().__init__(
            f'Cannot add {combined_verticals} to {service_name} because they are not supported.'
        )


class BaseTransferService(OAuth2Session, ABC):
    """
    A base class to be extended by service-specific classes that implement logic for
    OAuth 2.0 and data transfers.

    :param client_id: Client identifier given by the OAuth provider upon registration.
    :param client_secret: The `client_secret` paired to the `client_id`.
    :param redirect_url: the registered callback URI.
    """

    _supported_verticals: set[Vertical] = set()
    _verticals: set[Vertical] = set()
    _scope: set[str] = set()
    _service_name: str | None = None

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        background_application_client = BackendApplicationClient(client_id)
        super().__init__(
            client_id=client_id, client=background_application_client, redirect_uri=redirect_uri
        )

        self._client_secret = client_secret

    @property
    def name(self):
        return self._service_name

    @property
    def verticals(self) -> set[Vertical]:
        return self._verticals

    @verticals.setter
    def verticals(self, verticals: Iterable[Vertical]):
        """
        :raises: :class:`UnsupportedVerticalException`: if one or more of the
        `verticals` are not supported by the service.
        """
        unsupported_verticals = [
            vertical for vertical in verticals if vertical not in self._supported_verticals
        ]
        if len(unsupported_verticals) > 0:
            raise UnsupportedVerticalException(unsupported_verticals, self.name)
        self._verticals = set(verticals)

    def add_verticals(self, verticals: Iterable[Vertical], should_reauth: bool = False) -> bool:
        """
        Adds to the verticals being requested.

        :param verticals: `Vertical`s that should be added to service.
        :param should_reauth: whether or not the service should unauthorize itself to
        start a new session with added scopes corresponding to `verticals`.

        :returns: whether add was successful without reauthorization (`True`) or not
        (`False`).

        :raises: :class:`UnsupportedVerticalException`: if `should_reauth` is not
        passed and the current scopes are insufficient, this exception is raised.
        """
        new_verticals = set(verticals) - self.verticals
        new_scopes = self.scope_for_verticals(new_verticals)
        original_scopes: set = self.scope if self.scope else set()

        if not new_scopes.issubset(original_scopes) and not should_reauth:
            raise InsufficientScopeException(verticals, self.name)
        elif not new_scopes.issubset(original_scopes):
            self.verticals = new_verticals | self.verticals
            del self.access_token
            self.scope = original_scopes | new_scopes
            return False

        self.verticals = new_verticals | self.verticals
        return True

    @abstractmethod
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        """
        Given a vertical, returns the scopes necessary for making API requests for
        fetching data in that vertical.

        :param verticals: the verticals for which scopes are being requested.

        :returns: scope names corresponding to `verticals`.
        """
        pass
