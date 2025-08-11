import pytest

from pardner.verticals import Vertical

sample_scope = {'fake', 'scope'}


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'], [([], {'base'}), ([Vertical.FeedPost, {'base'}])]
)
def test_scope_for_vertical(mock_tumblr_transfer_service, verticals, expected_scope):
    assert mock_tumblr_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_fetch_token(mock_tumblr_transfer_service, mock_oAuth2Session):
    [mock_request, mock_response] = mock_oAuth2Session
    mock_tumblr_transfer_service.fetch_token(code='123code123')
    mock_request.assert_called_once()
    mock_response.assert_called_once()
