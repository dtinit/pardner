import pytest
from requests import HTTPError

from pardner.exceptions import UnsupportedRequestException, UnsupportedVerticalException
from pardner.verticals.physical_activity import PhysicalActivityVertical
from tests.test_transfer_services.conftest import NewVertical, mock_oauth2_session_get


def test_scope(mock_strava_transfer_service):
    mock_strava_transfer_service.scope == 'activity:read,profile:read_all'


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'],
    [([], set()), ([PhysicalActivityVertical], {'activity:read', 'profile:read_all'})],
)
def test_scope_for_verticals(mock_strava_transfer_service, verticals, expected_scope):
    assert mock_strava_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_scope_for_verticals_raises_error(mock_strava_transfer_service):
    with pytest.raises(UnsupportedVerticalException):
        mock_strava_transfer_service.scope_for_verticals([NewVertical])


def test_fetch_physical_activity_raises_exception(mock_strava_transfer_service):
    with pytest.raises(UnsupportedRequestException):
        mock_strava_transfer_service.fetch_physical_activity_vertical(count=31)


def test_fetch_physical_activity_vertical_raises_http_exception(
    mock_strava_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(HTTPError):
        mock_strava_transfer_service.fetch_physical_activity_vertical()


def test_fetch_physical_activity_vertical(mocker, mock_strava_transfer_service):
    sample_response = [{'object': 1}, {'object': 2}]

    response_object = mocker.MagicMock()
    response_object.json.return_value = sample_response

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert (
        mock_strava_transfer_service.fetch_physical_activity_vertical()
        == sample_response
    )
    assert (
        oauth2_session_get.call_args.args[1]
        == 'https://www.strava.com/api/v3/athlete/activities'
    )
