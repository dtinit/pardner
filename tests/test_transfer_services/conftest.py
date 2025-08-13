import pytest
from requests_oauthlib import OAuth2Session

from pardner.services.strava import StravaTransferService
from pardner.services.tumblr import TumblrTransferService
from pardner.verticals.base import Vertical


@pytest.fixture
def mock_oauth2_session_request(mocker):
    return mocker.patch('requests_oauthlib.OAuth2Session.request')


@pytest.fixture
def mock_oauth2_session_response(mocker):
    return mocker.patch(
        'oauthlib.oauth2.rfc6749.clients.WebApplicationClient.parse_request_body_response'
    )


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


def mock_oauth2_session_get(mocker, response_object):
    oauth2_session_get = mocker.patch.object(OAuth2Session, 'get', autospec=True)
    oauth2_session_get.return_value = response_object
    return oauth2_session_get
