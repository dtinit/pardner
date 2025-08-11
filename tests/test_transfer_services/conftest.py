import pytest

from pardner.services.strava import StravaTransferService
from pardner.services.tumblr import TumblrTransferService
from pardner.verticals.base import Vertical


@pytest.fixture
def mock_oAuth2Session(mocker):
    mock_oauth2session_request = mocker.patch('requests_oauthlib.OAuth2Session.request')
    mock_client_parse_request_body_response = mocker.patch(
        'oauthlib.oauth2.rfc6749.clients.WebApplicationClient.parse_request_body_response'
    )
    return [mock_oauth2session_request, mock_client_parse_request_body_response]


@pytest.fixture
def mock_vertical():
    Vertical.NEW_VERTICAL = 'new_vertical'
    Vertical.NEW_VERTICAL_EXTRA_SCOPE = 'new_vertical_unsupported'


@pytest.fixture
def mock_tumblr_transfer_service(verticals=[Vertical.FeedPost]):
    return TumblrTransferService(
        'fake_client_id', 'fake_client_secret', 'https://redirect_uri', None, verticals
    )


@pytest.fixture
def mock_strava_transfer_service(verticals=[Vertical.FeedPost]):
    return StravaTransferService(
        'fake_client_id', 'fake_client_secret', 'https://redirect_uri', None, verticals
    )
