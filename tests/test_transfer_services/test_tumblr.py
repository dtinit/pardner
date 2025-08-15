import pytest
from requests import HTTPError

from pardner.services.base import UnsupportedRequestException
from pardner.verticals import Vertical
from tests.test_transfer_services.conftest import mock_oauth2_session_get


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'], [([], {'basic'}), ([Vertical.FeedPost, {'basic'}])]
)
def test_scope_for_vertical(mock_tumblr_transfer_service, verticals, expected_scope):
    assert mock_tumblr_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_fetch_feed_posts_raises_exception(mock_tumblr_transfer_service):
    with pytest.raises(UnsupportedRequestException):
        mock_tumblr_transfer_service.fetch_feed_posts(count=21)


def test_fetch_feed_posts_raises_http_exception(
    mock_tumblr_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(HTTPError):
        mock_tumblr_transfer_service.fetch_feed_posts()


def test_fetch_feed_posts(mocker, mock_tumblr_transfer_service):
    response_object = mocker.MagicMock()
    response_object.json.return_value = {'response': {'posts': ['sample', 'posts']}}

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert mock_tumblr_transfer_service.fetch_feed_posts() == ['sample', 'posts']
    assert (
        oauth2_session_get.call_args.args[1]
        == 'https://api.tumblr.com/v2/user/dashboard'
    )
