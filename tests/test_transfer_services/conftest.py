import pytest
from requests import Response
from requests_oauthlib import OAuth2Session

from pardner.services.strava import StravaTransferService
from pardner.services.tumblr import TumblrTransferService
from pardner.verticals.base import Vertical

# FIXTURES


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
def mock_strava_transfer_service(verticals=[Vertical.PhysicalActivity]):
    return StravaTransferService(
        'fake_client_id', 'fake_client_secret', 'https://redirect_uri', None, verticals
    )


@pytest.fixture
def mock_oauth2_bad_response(mocker):
    mock_response = mocker.create_autospec(Response)
    mock_response.ok = False
    mock_response.status_code = 400
    mock_response.reason = 'fake reason'
    mock_response.url = 'fake url'
    mock_response.raise_for_status = lambda: Response.raise_for_status(mock_response)
    return mock_response


@pytest.fixture
def mock_oauth2_session_get_bad_response(mocker, mock_oauth2_bad_response):
    oauth2_session_get = mocker.patch.object(OAuth2Session, 'get', autospec=True)
    oauth2_session_get.return_value = mock_oauth2_bad_response
    return oauth2_session_get


# HELPERS


def mock_oauth2_session_get(mocker, response_object):
    oauth2_session_get = mocker.patch.object(OAuth2Session, 'get', autospec=True)
    oauth2_session_get.return_value = response_object
    return oauth2_session_get
