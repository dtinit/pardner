import pytest
from requests import HTTPError

from pardner.exceptions import UnsupportedRequestException
from pardner.verticals import SocialPostingVertical
from tests.test_transfer_services.conftest import mock_oauth2_session_get


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'],
    [([], {'basic'}), ([SocialPostingVertical, {'basic'}])],
)
def test_scope_for_vertical(tumblr_transfer_service, verticals, expected_scope):
    assert tumblr_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_fetch_social_posting_vertical_raises_exception(tumblr_transfer_service):
    with pytest.raises(UnsupportedRequestException):
        tumblr_transfer_service.fetch_social_posting_vertical(count=21)


def test_fetch_social_posting_vertical_raises_http_exception(
    tumblr_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(HTTPError):
        tumblr_transfer_service.fetch_social_posting_vertical()


def test_fetch_social_posting_vertical(mocker, tumblr_transfer_service):
    response_object = mocker.MagicMock()
    response_object.json.return_value = {'response': {'posts': ['sample', 'posts']}}

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert tumblr_transfer_service.fetch_social_posting_vertical() == [
        'sample',
        'posts',
    ]
    assert (
        oauth2_session_get.call_args.args[1]
        == 'https://api.tumblr.com/v2/user/dashboard'
    )


def test_fetch_primary_blog_id_already_set(tumblr_transfer_service):
    tumblr_transfer_service.primary_blog_id = 'existing-blog-id'
    assert tumblr_transfer_service.fetch_primary_blog_id() == 'existing-blog-id'


def test_fetch_primary_blog_id_success(mocker, tumblr_transfer_service):
    response_object = mocker.MagicMock()
    response_object.json.return_value = {
        'response': {
            'user': {
                'blogs': [
                    {'primary': False, 'uuid': 'secondary-blog-id'},
                    {'primary': True, 'uuid': 'primary-blog-id', 'name': 'my-blog'},
                    {'primary': False, 'uuid': 'another-secondary-id'},
                ]
            }
        }
    }
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert tumblr_transfer_service.fetch_primary_blog_id() == 'primary-blog-id'
    assert tumblr_transfer_service.primary_blog_id == 'primary-blog-id'
    assert oauth2_session_get.call_args.args[1] == 'https://api.tumblr.com/v2/user/info'


def test_fetch_primary_blog_id_raises_exception(
    tumblr_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(HTTPError):
        tumblr_transfer_service.fetch_primary_blog_id()
