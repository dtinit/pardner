from pardner.stateless.tumblr import (
    URLs,
    construct_authorization_url,
    fetch_token,
    scope_for_verticals,
)
from pardner.verticals import Vertical
from tests.conftest import get_url_params


def test_scope_for_verticals():
    assert scope_for_verticals({Vertical.FeedPost}) == {'base'}


def test_construct_authorization_url():
    auth_url, state = construct_authorization_url(
        'fake_client_id', 'https://redirect_uri'
    )
    assert auth_url.startswith(URLs.AuthorizationURL)

    auth_url_params = get_url_params(auth_url)

    assert 'client_id' in auth_url_params
    assert auth_url_params['client_id'] == 'fake_client_id'
    assert 'redirect_uri' in auth_url_params
    assert auth_url_params['redirect_uri'] == 'https://redirect_uri'
    assert 'state' in auth_url_params
    assert auth_url_params['state'] == state
    assert 'scope' in auth_url_params
    assert 'base' in auth_url_params['scope']


def test_fetch_token_with_code(mock_outbound_requests):
    mock_oauth2session_request, mock_client_parse_request_body_response = (
        mock_outbound_requests
    )
    fetch_token(
        'fake_client_id',
        'https://redirect_uri',
        client_secret='fake client secret',
        code='the_best_code',
    )
    mock_oauth2session_request.assert_called_once()
    mock_client_parse_request_body_response.assert_called_once()
