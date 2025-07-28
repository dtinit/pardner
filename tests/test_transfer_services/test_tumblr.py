from urllib import parse

import pytest

from pardner.services import TumblrTransferService
from pardner.verticals import Vertical

sample_scope = {'fake', 'scope'}


@pytest.fixture
def mock_tumblr_transfer_service(monkeypatch, verticals=[Vertical.FeedPost]):
    return TumblrTransferService(
        'fake_client_id', 'fake_client_secret', 'https://redirect_uri', verticals
    )


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'], [([], {'base'}), ([Vertical.FeedPost, {'base'}])]
)
def test_scope_for_vertical(mock_tumblr_transfer_service, verticals, expected_scope):
    assert mock_tumblr_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_authorization_url(mock_tumblr_transfer_service):
    auth_url, state = mock_tumblr_transfer_service.authorization_url()

    auth_url_query = parse.urlsplit(auth_url).query
    auth_url_params = dict(parse.parse_qsl(auth_url_query))

    assert 'client_id' in auth_url_params
    assert auth_url_params['client_id'] == 'fake_client_id'
    assert 'redirect_uri' in auth_url_params
    assert auth_url_params['redirect_uri'] == 'https://redirect_uri'
    assert 'state' in auth_url_params
    assert auth_url_params['state'] == state


def test_fetch_token_raises_error(mock_tumblr_transfer_service):
    with pytest.raises(ValueError):
        mock_tumblr_transfer_service.fetch_token()


def test_fetch_token(mocker, mock_tumblr_transfer_service):
    mock_oauth2session_request = mocker.patch('requests_oauthlib.OAuth2Session.request')
    mock_client_parse_request_body_response = mocker.patch(
        'oauthlib.oauth2.rfc6749.clients.WebApplicationClient.parse_request_body_response'
    )
    mock_tumblr_transfer_service.fetch_token(code='123code123')
    mock_oauth2session_request.assert_called_once()
    mock_client_parse_request_body_response.assert_called_once()
