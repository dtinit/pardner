import pytest

from pardner.services.base import UnsupportedVerticalException
from pardner.verticals import Vertical

sample_scope = {'fake', 'scope'}


def test_scope(mock_strava_transfer_service):
    mock_strava_transfer_service.scope == 'activity:read,profile:read_all'


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'],
    [([], set()), ([Vertical.FeedPost], {'activity:read', 'profile:read_all'})],
)
def test_scope_for_verticals(mock_strava_transfer_service, verticals, expected_scope):
    assert mock_strava_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_scope_for_verticals_raises_error(mock_strava_transfer_service, mock_vertical):
    with pytest.raises(UnsupportedVerticalException):
        mock_strava_transfer_service.scope_for_verticals([Vertical.NEW_VERTICAL])


def test_fetch_token(mock_oAuth2Session, mock_strava_transfer_service):
    [mock_request, _] = mock_oAuth2Session
    mock_strava_transfer_service.fetch_token(code='123code123')
    mock_request.assert_called_once()
    assert 'client_id' in mock_request.call_args.kwargs['data']
    assert mock_request.call_args.kwargs['data']['client_id'] == 'fake_client_id'
