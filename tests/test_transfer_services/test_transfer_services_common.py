import pytest

from pardner.exceptions import UnsupportedVerticalException
from pardner.verticals import Vertical


@pytest.mark.parametrize(
    'transfer_service_fixture_name',
    ['tumblr_transfer_service', 'strava_transfer_service'],
)
def test_fetch_token(
    mock_oauth2_session_request,
    mock_oauth2_session_response,
    request,
    transfer_service_fixture_name,
):
    mock_transfer_service = request.getfixturevalue(transfer_service_fixture_name)
    mock_transfer_service.fetch_token(code='123code123')
    mock_oauth2_session_request.assert_called_once()
    assert 'client_id' in mock_oauth2_session_request.call_args.kwargs['data']
    assert (
        mock_oauth2_session_request.call_args.kwargs['data']['client_id']
        == 'fake_client_id'
    )


@pytest.mark.parametrize(
    'transfer_service_fixture_name',
    ['tumblr_transfer_service', 'strava_transfer_service', 'groupme_transfer_service'],
)
def test_fetch_vertical_generic(
    request, mock_oauth2_session_get_good_response, transfer_service_fixture_name
):
    mock_transfer_service = request.getfixturevalue(transfer_service_fixture_name)
    for vertical in Vertical:
        if not mock_transfer_service.is_vertical_supported(vertical):
            with pytest.raises(UnsupportedVerticalException):
                mock_transfer_service.fetch(vertical)
        else:
            mock_transfer_service.fetch(vertical)
