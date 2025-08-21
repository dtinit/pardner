import pytest

from pardner.exceptions import UnsupportedRequestException
from tests.test_transfer_services.conftest import mock_oauth2_session_get

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


@pytest.mark.parametrize(
    [
        'method_name',
        'json_response',
        'expected_path',
        'expected_params',
        'expected_return_val',
    ],
    [
        (
            'fetch_blocked_users',
            {'response': {'blocks': FAKE_LIST_RESPONSE}},
            'https://api.groupme.com/v3/blocks',
            {},
            FAKE_LIST_RESPONSE,
        ),
        (
            'fetch_chat_bots',
            {'response': FAKE_LIST_RESPONSE},
            'https://api.groupme.com/v3/bots',
            {},
            FAKE_LIST_RESPONSE,
        ),
        (
            'fetch_conversations_direct',
            {'response': FAKE_LIST_RESPONSE},
            'https://api.groupme.com/v3/chats',
            {'per_page': 10},
            FAKE_LIST_RESPONSE,
        ),
        (
            'fetch_conversations_group',
            {'response': FAKE_LIST_RESPONSE},
            'https://api.groupme.com/v3/groups',
            {'per_page': 10},
            FAKE_LIST_RESPONSE,
        ),
    ],
)
def test_fetch_vertical(
    method_name,
    json_response,
    expected_path,
    expected_params,
    expected_return_val,
    mock_groupme_transfer_service,
    mocker,
):
    full_expected_params = {'user': USER_ID, 'token': TOKEN, **expected_params}

    mock_groupme_transfer_service._user_id = USER_ID

    response_object = mocker.MagicMock()
    response_object.json.return_value = json_response

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    assert getattr(mock_groupme_transfer_service, method_name)() == expected_return_val
    assert oauth2_session_get.call_args.args[1] == expected_path
    assert oauth2_session_get.call_args.kwargs.get('params') == full_expected_params


@pytest.mark.parametrize(
    'method_name', ['fetch_conversations_direct', 'fetch_conversations_group']
)
def test_fetch_conversations_raises_exception(
    method_name, mock_groupme_transfer_service
):
    with pytest.raises(UnsupportedRequestException):
        getattr(mock_groupme_transfer_service, method_name)(count=11)


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


def test_fetch_blocked_users_raises_exception(mock_groupme_transfer_service, mocker):
    mock_groupme_transfer_service._user_id = USER_ID
    response_object = mocker.MagicMock()
    response_object.status_code = 200
    response_object.json.return_value = {'response': {'no_blocks': []}}
    mock_oauth2_session_get(mocker, response_object)
    with pytest.raises(ValueError):
        mock_groupme_transfer_service.fetch_blocked_users()
