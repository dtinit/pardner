from datetime import datetime, timezone

import pytest
from pydantic import AnyHttpUrl

from pardner.exceptions import UnsupportedRequestException
from tests.test_transfer_services.conftest import (
    dump_and_filter_model_objs,
    mock_oauth2_session_get,
)

USER_ID = 'fake_user_id'
FAKE_LIST_RESPONSE = ['fake', 'list', 'response']
TOKEN = 'fake_token'


def test_fetch_token_raises_no_authorization_response(mock_groupme_transfer_service):
    with pytest.raises(ValueError):
        mock_groupme_transfer_service.fetch_token(code='code')


def test_fetch_token_raises_no_access_token(mock_groupme_transfer_service):
    with pytest.raises(ValueError):
        mock_groupme_transfer_service.fetch_token(
            authorization_response='https://localhostfake?token=badtoken'
        )


def test_fetch_token(mock_oauth2_session_request, mock_groupme_transfer_service):
    token = 'faketoken123'
    mock_groupme_transfer_service.fetch_token(
        authorization_response=f'https://localhostfake?access_token={token}'
    )
    mock_oauth2_session_request.assert_not_called()
    assert (
        mock_groupme_transfer_service._oAuth2Session.token.get('access_token', {})
        == token
    )


def test__fetch_resource_common_raises_exception(mock_groupme_transfer_service, mocker):
    response_object = mocker.MagicMock()
    response_object.status_code = 200
    response_object.json.return_value = {'response': {'id': USER_ID}}
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    mock_groupme_transfer_service._fetch_resource_common(
        'https://api.groupme.com/v3/fake'
    )

    assert oauth2_session_get.call_count == 2
    assert mock_groupme_transfer_service._user_id == USER_ID


def test_fetch_user_data_raises_no_token(mock_groupme_transfer_service):
    mock_groupme_transfer_service._oAuth2Session.token = {}
    with pytest.raises(UnsupportedRequestException):
        mock_groupme_transfer_service.fetch_user_data()


def test_fetch_user_data(mocker, mock_groupme_transfer_service):
    expected_respose = {'id': USER_ID}
    response_object = mocker.MagicMock()
    response_object.json.return_value = {'response': expected_respose}
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert mock_groupme_transfer_service.fetch_user_data() == expected_respose
    assert mock_groupme_transfer_service._user_id == USER_ID
    assert oauth2_session_get.call_args.args[1] == 'https://api.groupme.com/v3/users/me'


def test_fetch_blocked_users_raises_exception(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    response_object.status_code = 200
    response_object.json.return_value = {'response': {'no_blocks': []}}
    mock_oauth2_session_get(mocker, response_object)
    with pytest.raises(ValueError):
        mock_groupme_transfer_service.fetch_blocked_user_vertical()


def test_fetch_blocked_user_vertical(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    # adapted from
    # https://dev.groupme.com/docs/v3#blocks_index
    response_object.json.return_value = {
        'response': {
            'blocks': [
                {
                    'user_id': USER_ID,
                    'blocked_user_id': '1234567890',
                    'created_at': 1302623328,
                },
                {'blocked_user_id': '12345678901', 'created_at': 1302623348},
            ]
        }
    }
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)
    model_objs, _ = mock_groupme_transfer_service.fetch_blocked_user_vertical()
    model_obj_dumps = dump_and_filter_model_objs(model_objs)

    assert oauth2_session_get.call_args.args[1] == 'https://api.groupme.com/v3/blocks'

    base_model_dict = {
        'service_object_id': None,
        'creator_user_id': None,
        'data_owner_id': USER_ID,
        'service': 'GroupMe',
        'url': None,
        'vertical_name': 'blocked_user',
    }

    assert model_obj_dumps == [
        {
            **base_model_dict,
            'creator_user_id': USER_ID,
            'created_at': datetime(2011, 4, 12, 15, 48, 48, tzinfo=timezone.utc),
            'blocked_user_id': '1234567890',
        },
        {
            **base_model_dict,
            'created_at': datetime(2011, 4, 12, 15, 49, 8, tzinfo=timezone.utc),
            'blocked_user_id': '12345678901',
        },
    ]


def test_fetch_chat_bot_vertical(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    # adapted from
    # https://dev.groupme.com/docs/v3#bots_index
    response_object.json.return_value = {
        'response': [
            {
                'bot_id': '1234567890',
                'group_id': '1234567890',
                'name': 'hal9000',
                'avatar_url': 'https://i.groupme.com/123456789',
                'callback_url': 'https://example.com/bots/callback',
                'dm_notification': False,
                'active': True,
            },
            {
                'bot_id': '123',
                'name': 'hal9001',
                'avatar_url': 'https://i.groupme.com/123456789',
                'callback_url': 'https://example.com/bots/callback',
            },
        ]
    }
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)
    model_objs, _ = mock_groupme_transfer_service.fetch_chat_bot_vertical()

    assert oauth2_session_get.call_args.args[1] == 'https://api.groupme.com/v3/bots'

    model_obj_dumps = dump_and_filter_model_objs(model_objs)

    base_model_dict = {
        'creator_user_id': USER_ID,
        'data_owner_id': USER_ID,
        'service': 'GroupMe',
        'vertical_name': 'chat_bot',
        'created_at': None,
        'url': None,
    }

    assert model_obj_dumps == [
        {**base_model_dict, 'service_object_id': '1234567890', 'name': 'hal9000'},
        {**base_model_dict, 'service_object_id': '123', 'name': 'hal9001'},
    ]


@pytest.mark.parametrize(
    'method_name',
    ['fetch_conversation_direct_vertical', 'fetch_conversation_group_vertical'],
)
def test_fetch_conversations_raises_exception(
    method_name, mock_groupme_transfer_service
):
    with pytest.raises(UnsupportedRequestException):
        getattr(mock_groupme_transfer_service, method_name)(count=11)


def test_fetch_conversation_direct_vertical(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    # adapted from
    # https://dev.groupme.com/docs/v3#chats_index
    response_object.json.return_value = {
        'response': [
            {
                'created_at': 1352299338,
                'updated_at': 1352299338,
                'last_message': {
                    'attachments': [],
                    'avatar_url': 'https://i.groupme.com/200x200.jpeg.abcdef',
                    'conversation_id': '12345+67890',
                    'created_at': 1352299338,
                    'favorited_by': [],
                    'id': '1234567890',
                    'name': 'John Doe',
                    'recipient_id': '67890',
                    'sender_id': '12345',
                    'sender_type': 'user',
                    'source_guid': 'GUID',
                    'text': 'Hello world',
                    'user_id': '12345',
                },
                'messages_count': 10,
                'other_user': {
                    'avatar_url': 'https://i.groupme.com/200x200.jpeg.abcdef',
                    'id': 12345,
                    'name': 'John Doe',
                },
            },
            {
                'created_at': 1668785830,
                'last_message': {
                    'attachments': [
                        {
                            'type': 'image',
                            'url': 'https://i.groupme.com/351x672.png.101010',
                        }
                    ],
                    'avatar_url': None,
                    'conversation_id': '101010+202020',
                    'created_at': 1668785830,
                    'favorited_by': [],
                    'id': '166116611',
                    'name': 'Gabriel',
                    'recipient_id': '101010',
                    'sender_id': '202020',
                    'sender_type': 'user',
                    'source_guid': 'caabcdef',
                    'text': None,
                    'user_id': '202020',
                    'pinned_at': None,
                    'pinned_by': '',
                },
                'messages_count': 1,
                'other_user': {
                    'avatar_url': 'https://i.groupme.com/512x512.jpeg.1010',
                    'id': '101010',
                    'name': 'Gabriel',
                },
                'updated_at': 1668785830,
                'message_deletion_period': 2147483647,
                'message_deletion_mode': ['sender'],
                'requires_approval': False,
                'unread_count': None,
                'last_read_message_id': None,
                'last_read_at': None,
                'message_edit_period': 15,
            },
        ]
    }
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)
    model_objs, _ = mock_groupme_transfer_service.fetch_conversation_direct_vertical()

    assert oauth2_session_get.call_args.args[1] == 'https://api.groupme.com/v3/chats'

    model_obj_dumps = dump_and_filter_model_objs(model_objs)

    base_model_dict = {
        'service_object_id': None,
        'creator_user_id': None,
        'data_owner_id': USER_ID,
        'service': 'GroupMe',
        'vertical_name': 'conversation_direct',
        'url': None,
        'is_group_conversation': False,
        'abstract': None,
        'associated_media': [],
        'is_private': None,
        'members_count': 2,
        'title': None,
    }

    assert model_obj_dumps == [
        {
            **base_model_dict,
            'created_at': datetime(2012, 11, 7, 14, 42, 18, tzinfo=timezone.utc),
            'member_user_ids': [USER_ID, '12345'],
            'messages_count': 10,
        },
        {
            **base_model_dict,
            'created_at': datetime(2022, 11, 18, 15, 37, 10, tzinfo=timezone.utc),
            'member_user_ids': [USER_ID, '101010'],
            'messages_count': 1,
        },
    ]


def test_fetch_conversation_group_vertical(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    # adapted from
    # https://dev.groupme.com/docs/v3#groups_index
    response_object.json.return_value = {
        'response': [
            {
                'id': '1234567890',
                'name': 'Family',
                'type': 'private',
                'description': 'Coolest Family Ever',
                'image_url': 'https://i.groupme.com/123456789',
                'creator_user_id': USER_ID,
                'created_at': 1302623328,
                'updated_at': 1302623328,
                'members': [
                    {
                        'user_id': USER_ID,
                        'nickname': 'Jane',
                        'muted': False,
                        'image_url': 'https://i.groupme.com/123456789',
                    }
                ],
                'share_url': 'https://groupme.com/join_group/1234567890/SHARE_TOKEN',
                'messages': {
                    'count': 100,
                    'last_message_id': '1234567890',
                    'last_message_created_at': 1302623328,
                    'preview': {
                        'nickname': 'Jane',
                        'text': 'Hello world',
                        'image_url': 'https://i.groupme.com/123456789',
                        'attachments': [
                            {'type': 'image', 'url': 'https://i.groupme.com/123456789'},
                            {'type': 'image', 'url': 'https://i.groupme.com/123456789'},
                            {
                                'type': 'location',
                                'lat': '40.738206',
                                'lng': '-73.993285',
                                'name': 'GroupMe HQ',
                            },
                            {'type': 'split', 'token': 'SPLIT_TOKEN'},
                            {
                                'type': 'emoji',
                                'placeholder': '☃',
                                'charmap': [[1, 42], [2, 34]],
                            },
                        ],
                    },
                },
            },
            {
                'id': '111111',
                'group_id': '111111',
                'name': 'Second Group',
                'phone_number': '+199999999999',
                'type': 'closed',
                'description': "Hey y'all!",
                'image_url': None,
                'creator_user_id': 'u222222',
                'created_at': 1554220666,
                'updated_at': 1579220489,
                'muted_until': None,
                'messages': {
                    'count': 380,
                    'last_message_id': '101010',
                    'last_message_created_at': 1579220489,
                    'last_message_updated_at': 1579220489,
                    'preview': {
                        'nickname': 'Kenneth',
                        'text': 'these are cool',
                        'image_url': 'https://i.groupme.com/1818x1228.jpeg',
                        'attachments': [],
                    },
                },
                'max_members': 5000,
                'theme_name': None,
                'like_icon': None,
                'requires_approval': False,
                'show_join_question': False,
                'join_question': None,
                'message_deletion_period': 2147483647,
                'message_deletion_mode': ['admin', 'sender'],
                'message_edit_period': 15,
                'children_count': 0,
                'share_url': None,
                'share_qr_code_url': None,
                'directories': None,
                'members': [
                    {
                        'user_id': USER_ID,
                        'nickname': 'Member1',
                        'image_url': 'https://i.groupme.com/750x750.jpeg',
                        'id': USER_ID,
                        'muted': False,
                        'autokicked': False,
                        'roles': ['admin', 'owner'],
                        'name': 'Member1',
                    },
                    {
                        'user_id': 'u222222',
                        'nickname': 'Member2',
                        'image_url': 'https://i.groupme.com/960x720.jpeg',
                        'id': 'u222222',
                        'muted': False,
                        'autokicked': False,
                        'roles': ['user'],
                        'name': 'Member2',
                    },
                ],
                'members_count': 2,
                'locations': None,
                'visibility': None,
                'category_ids': None,
                'active_call_participants': None,
                'unread_count': None,
                'last_read_message_id': None,
                'last_read_at': None,
            },
        ]
    }
    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)
    model_objs, _ = mock_groupme_transfer_service.fetch_conversation_group_vertical()

    assert oauth2_session_get.call_args.args[1] == 'https://api.groupme.com/v3/groups'

    model_obj_dumps = dump_and_filter_model_objs(model_objs)

    base_model_dict = {
        'creator_user_id': USER_ID,
        'data_owner_id': USER_ID,
        'service': 'GroupMe',
        'vertical_name': 'conversation_group',
        'url': None,
        'is_group_conversation': True,
        'abstract': None,
        'associated_media': [],
        'is_private': None,
    }

    assert model_obj_dumps == [
        {
            **base_model_dict,
            'service_object_id': '1234567890',
            'created_at': datetime(2011, 4, 12, 15, 48, 48, tzinfo=timezone.utc),
            'associated_media': [
                {
                    'audio_url': None,
                    'image_url': AnyHttpUrl('https://i.groupme.com/123456789'),
                    'video_url': None,
                }
            ],
            'is_private': True,
            'member_user_ids': [USER_ID],
            'members_count': 1,
            'messages_count': 100,
            'title': 'Family',
        },
        {
            **base_model_dict,
            'creator_user_id': 'u222222',
            'service_object_id': '111111',
            'created_at': datetime(2019, 4, 2, 15, 57, 46, tzinfo=timezone.utc),
            'is_private': False,
            'member_user_ids': [USER_ID, 'u222222'],
            'members_count': 2,
            'messages_count': 380,
            'title': 'Second Group',
        },
    ]
