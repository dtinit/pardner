from typing import Any, Optional, TypeAlias

from requests_oauthlib import OAuth2Session

Scope: TypeAlias = str | set[object] | tuple[object] | list[object]


def generic_construct_authorization_url(
    authorization_url_endpoint: str, client_id: str, redirect_uri: str, scope: Scope
) -> tuple[str, str]:
    """
    Builds the authorization URL and state. Once the end-user (i.e., resource owner)
    navigates to the authorization URL they can begin the authorization flow.

    :param authorization_url_endpoint: The service's endpoint that must be hit to begin
    the OAuth 2 flow.
    :param client_id: Client identifier given by the OAuth provider upon registration.
    :param redirect_uri: The registered callback URI.
    :param scope: The scope of the access request. These may be any string but are
    commonly URIs or various categories such as ``videos`` or ``documents``.

    :returns: the authorization URL and state, respectively.
    """
    oAuth2Session = OAuth2Session(
        client_id=client_id, redirect_uri=redirect_uri, scope=scope
    )
    return oAuth2Session.authorization_url(authorization_url_endpoint)


def generic_fetch_token(
    client_id: str,
    redirect_uri: str,
    scope: Scope,
    token_url: str,
    authorization_response: Optional[str] = None,
    client_secret: Optional[str] = None,
    code: Optional[str] = None,
    include_client_id: Optional[bool] = None,
) -> dict[str, Any]:
    """
    Once the end-user authorizes the application to access their data, the
    resource server sends a request to `redirect_uri` with the authorization code as
    a parameter. Using this authorization code, this method makes a request to the
    resource server to obtain the access token.

    One of either `code` or `authorization_response` must not be None.

    :param authorization_url_endpoint: The service's endpoint that must be hit to begin
    the OAuth 2 flow.
    :param client_id: Client identifier given by the OAuth provider upon registration.
    :param redirect_uri: The registered callback URI.
    :param scope: The scope of the access request. These may be any string but are
    commonly URIs or various categories such as ``videos`` or ``documents``.
    :param authorization_response: the URL (with parameters) the end-user's browser
    redirected to after authorization.
    :param client_secret: The `client_secret` paired to the `client_id`.
    :param code: Authorization code (used by WebApplicationClients).
    :param include_client_id: Should the request body include the
    `client_id` parameter.

    :returns: the authorization URL and state, respectively.
    """
    oAuth2Session = OAuth2Session(
        client_id=client_id, redirect_uri=redirect_uri, scope=scope
    )
    return oAuth2Session.fetch_token(
        token_url=token_url,
        code=code,
        authorization_response=authorization_response,
        include_client_id=include_client_id,
        client_secret=client_secret,
    )
