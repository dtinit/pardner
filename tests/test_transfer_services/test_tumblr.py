import datetime

import pytest
from pydantic import AnyHttpUrl

from pardner.exceptions import TumblrAPIError, UnsupportedRequestException
from pardner.verticals import SocialPostingVertical
from tests.test_transfer_services.conftest import (
    dump_and_filter_model_objs,
    mock_oauth2_session_get,
)


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'],
    [([], {'basic'}), ([SocialPostingVertical, {'basic'}])],
)
def test_scope_for_vertical(tumblr_transfer_service, verticals, expected_scope):
    assert tumblr_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_fetch_social_posting_vertical_raises_exception(tumblr_transfer_service):
    with pytest.raises(UnsupportedRequestException):
        tumblr_transfer_service.fetch_social_posting_vertical(count=21)


def test_fetch_social_posting_vertical_raises_tumblr_api_error_on_http_error(
    tumblr_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(TumblrAPIError):
        tumblr_transfer_service.fetch_social_posting_vertical()


def test_fetch_social_posting_vertical(mocker, tumblr_transfer_service):
    sample_post = {
        'id': 123456,
        'post_url': 'https://example.tumblr.com/post/123456',
        'timestamp': 1700000000,
        'summary': 'A test post',
        'note_count': 42,
        'tags': ['python', 'testing'],
        'state': 'published',
        'blog': {'uuid': 'author-uuid', 'name': 'author-blog'},
        'content': [
            {'type': 'text', 'text': 'Hello world'},
            {
                'type': 'image',
                'media': [{'url': 'https://example.com/image.jpg', 'width': 800}],
            },
        ],
    }
    response_object = mocker.MagicMock()
    response_object.json.return_value = {'response': {'posts': [sample_post]}}

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    parsed, raw_posts = tumblr_transfer_service.fetch_social_posting_vertical()

    assert (
        oauth2_session_get.call_args.args[1]
        == 'https://api.tumblr.com/v2/user/dashboard'
    )
    assert raw_posts == [sample_post]
    assert len(parsed) == 1

    model_obj_dump = dump_and_filter_model_objs(parsed)[0]

    assert model_obj_dump == {
        'service': 'Tumblr',
        'vertical_name': 'social_posting',
        'service_object_id': '123456',
        'creator_user_id': 'author-uuid',
        'data_owner_id': '',
        'created_at': datetime.datetime(2023, 11, 14, 22, 13, 20),
        'url': AnyHttpUrl('https://example.tumblr.com/post/123456'),
        'abstract': 'A test post',
        'interaction_count': 42,
        'keywords': ['python', 'testing'],
        'shared_content': [],
        'status': 'public',
        'text': 'Hello world',
        'title': None,
        'associated_media': [
            {'media_type': 'image', 'url': AnyHttpUrl('https://example.com/image.jpg')}
        ],
    }


@pytest.mark.parametrize(
    'bad_payload',
    [
        {},
        {'response': {'posts': None}},
    ],
)
def test_fetch_social_posting_vertical_raises_tumblr_api_error_on_bad_payload(
    mocker, tumblr_transfer_service, bad_payload
):
    response_object = mocker.MagicMock()
    response_object.json.return_value = bad_payload
    mock_oauth2_session_get(mocker, response_object)

    with pytest.raises(TumblrAPIError):
        tumblr_transfer_service.fetch_social_posting_vertical()


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


def test_fetch_primary_blog_id_raises_tumblr_api_error_on_http_error(
    tumblr_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(TumblrAPIError):
        tumblr_transfer_service.fetch_primary_blog_id()


@pytest.mark.parametrize(
    'bad_payload',
    [
        {},
        {'response': {'user': {'blogs': None}}},
    ],
)
def test_fetch_primary_blog_id_raises_tumblr_api_error_on_bad_payload(
    mocker, tumblr_transfer_service, bad_payload
):
    response_object = mocker.MagicMock()
    response_object.json.return_value = bad_payload
    mock_oauth2_session_get(mocker, response_object)

    with pytest.raises(TumblrAPIError):
        tumblr_transfer_service.fetch_primary_blog_id()


def test_parse_social_posting_vertical_returns_none_for_non_dict(
    tumblr_transfer_service,
):
    assert tumblr_transfer_service.parse_social_posting_vertical(None) is None
    assert tumblr_transfer_service.parse_social_posting_vertical('string') is None
    assert tumblr_transfer_service.parse_social_posting_vertical([]) is None


def test_parse_social_posting_vertical_minimal(tumblr_transfer_service):
    result = tumblr_transfer_service.parse_social_posting_vertical({})
    assert isinstance(result, SocialPostingVertical)
    assert result.service_object_id is None
    assert result.text is None
    assert result.associated_media == []
    assert result.keywords == []


def test_parse_social_posting_vertical_maps_state(tumblr_transfer_service):
    for tumblr_state, expected_status in [
        ('published', 'public'),
        ('private', 'private'),
        ('draft', 'draft'),
        ('queued', 'restricted'),
        ('queue', 'restricted'),
    ]:
        result = tumblr_transfer_service.parse_social_posting_vertical(
            {'state': tumblr_state}
        )
        assert result.status == expected_status, f'Failed for state={tumblr_state}'


def test_parse_social_posting_vertical_text_blocks(tumblr_transfer_service):
    raw = {
        'content': [
            {'type': 'text', 'text': 'First paragraph'},
            {'type': 'text', 'text': 'Second paragraph'},
        ]
    }
    result = tumblr_transfer_service.parse_social_posting_vertical(raw)
    assert result.text == 'First paragraph\n\nSecond paragraph'


def test_parse_social_posting_vertical_media_blocks(tumblr_transfer_service):
    raw = {
        'content': [
            {
                'type': 'image',
                'media': [
                    {'url': 'https://example.com/img1.jpg'},
                    {'url': 'https://example.com/img2.jpg'},
                ],
            },
            {
                'type': 'video',
                'media': {'url': 'https://example.com/vid.mp4'},
            },
        ]
    }
    result = tumblr_transfer_service.parse_social_posting_vertical(raw)
    assert len(result.associated_media) == 3
    assert result.associated_media[0].media_type == 'image'
    assert result.associated_media[2].media_type == 'video'
