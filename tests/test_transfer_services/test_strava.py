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
