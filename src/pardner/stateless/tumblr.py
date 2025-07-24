from enum import StrEnum
from typing import Any, Iterable, Optional

from pardner.stateless import Scope
from pardner.stateless.base import (
    generic_construct_authorization_url,
    generic_fetch_token,
)
from pardner.verticals import Vertical


class URLs(StrEnum):
    AuthorizationURL = 'https://www.tumblr.com/oauth2/authorize'
    TokenURL = 'https://api.tumblr.com/v2/oauth2/token'


def scope_for_verticals(verticals: Iterable[Vertical]) -> set[str]:
    # Tumblr only needs 'base' for read access requests
    return {'base'}


def construct_authorization_url(
    client_id: str, redirect_uri: str, scope: Scope = {'base'}
) -> tuple[str, str]:
    """
    Builds the authorization URL and state for Tumblr.

    :param client_id: Client identifier given by the OAuth provider upon registration.
    :param redirect_uri: The registered callback URI.
    :param scope: The scope of the access request. These may be any string but are
    commonly URIs or various categories such as ``videos`` or ``documents``.

    :returns: the authorization URL and state, respectively.
    """
    return generic_construct_authorization_url(
        URLs.AuthorizationURL, client_id, redirect_uri, scope
    )


def fetch_token(
    client_id: str,
    redirect_uri: str,
    authorization_response: Optional[str] = None,
    client_secret: Optional[str] = None,
    code: Optional[str] = None,
) -> dict[str, Any]:
    """
    Makes a request to Tumblr's resource server to obtain the access token.

    One of either `code` or `authorization_response` must not be None.

    :param client_id: Client identifier given by the OAuth provider upon registration.
    :param redirect_uri: The registered callback URI.
    :param scope: The scope of the access request. These may be any string but are
    commonly URIs or various categories such as ``videos`` or ``documents``.
    :param authorization_response: the URL (with parameters) the end-user's browser
    redirected to after authorization.
    :param client_secret: The `client_secret` paired to the `client_id`.
    :param code: Authorization code (used by WebApplicationClients).

    :returns: the authorization URL and state, respectively.
    """
    return generic_fetch_token(
        client_id,
        redirect_uri,
        {'base'},
        URLs.TokenURL,
        authorization_response,
        client_secret,
        code,
        include_client_id=True,
    )
