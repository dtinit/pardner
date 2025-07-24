import pytest

from pardner.services import TumblrTransferService
from pardner.verticals import Vertical
from tests.conftest import get_url_params

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

    auth_url_params = get_url_params(auth_url)

    assert 'client_id' in auth_url_params
    assert auth_url_params['client_id'] == 'fake_client_id'
    assert 'redirect_uri' in auth_url_params
    assert auth_url_params['redirect_uri'] == 'https://redirect_uri'
    assert 'state' in auth_url_params
    assert auth_url_params['state'] == state


def test_fetch_token_raises_error(mock_tumblr_transfer_service):
    with pytest.raises(ValueError):
        mock_tumblr_transfer_service.fetch_token()


def test_fetch_token(mock_tumblr_transfer_service, mock_outbound_requests):
    mock_oauth2session_request, mock_client_parse_request_body_response = (
        mock_outbound_requests
    )
    mock_tumblr_transfer_service.fetch_token(code='123code123')
    mock_oauth2session_request.assert_called_once()
    mock_client_parse_request_body_response.assert_called_once()
