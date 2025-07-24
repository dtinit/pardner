import pytest

from pardner.stateless.base import (
    generic_construct_authorization_url,
    generic_fetch_token,
)
from tests.conftest import get_url_params


def test_generic_construct_authorization_url():
    auth_url, state = generic_construct_authorization_url(
        'https://authorize.com',
        'fake_client_id',
        'https://redirect_uri',
        {'fake', 'scope'},
    )
    assert auth_url.startswith('https://authorize.com')

    auth_url_params = get_url_params(auth_url)

    assert 'client_id' in auth_url_params
    assert auth_url_params['client_id'] == 'fake_client_id'
    assert 'redirect_uri' in auth_url_params
    assert auth_url_params['redirect_uri'] == 'https://redirect_uri'
    assert 'state' in auth_url_params
    assert auth_url_params['state'] == state
    assert 'scope' in auth_url_params
    assert 'fake' in auth_url_params['scope']
    assert 'scope' in auth_url_params['scope']


def test_generic_fetch_token_raises_error():
    with pytest.raises(ValueError):
        generic_fetch_token(
            'fake_client_id',
            'https://redirect_uri',
            {'fake', 'scope'},
            'https://token_url.com',
            authorization_response=None,
            client_secret='fake client secret',
            code=None,
        )


def test_generic_fetch_token_with_code(mock_outbound_requests):
    mock_oauth2session_request, mock_client_parse_request_body_response = (
        mock_outbound_requests
    )
    generic_fetch_token(
        'fake_client_id',
        'https://redirect_uri',
        {'fake', 'scope'},
        'https://token_url.com',
        client_secret='fake client secret',
        code='the_best_code',
    )
    mock_oauth2session_request.assert_called_once()
    mock_client_parse_request_body_response.assert_called_once()


def test_generic_fetch_token_with_authorization_response(mock_outbound_requests):
    mock_oauth2session_request, mock_client_parse_request_body_response = (
        mock_outbound_requests
    )
    generic_fetch_token(
        'fake_client_id',
        'https://redirect_uri',
        {'fake', 'scope'},
        'https://token_url.com',
        authorization_response='https://redirect/?code=the_best_code',
        client_secret='fake client secret',
    )
    mock_oauth2session_request.assert_called_once()
    mock_client_parse_request_body_response.assert_called_once()
