from urllib import parse

import pytest

from pardner.services import (
    BaseTransferService,
    InsufficientScopeException,
    UnsupportedVerticalException,
)
from pardner.verticals import SocialPostingVertical
from tests.test_transfer_services.conftest import ExtraScopeVertical, NewVertical

SAMPLE_SCOPE = {'fake', 'scope'}
SAMPLE_BASE_URL = 'https://api.example.com/v1'


class FakeTransferService(BaseTransferService):
    _authorization_url = 'https://auth_url'
    _base_url = SAMPLE_BASE_URL
    _token_url = 'https://token_url'

    def __init__(self, supported_verticals, verticals):
        super().__init__(
            service_name='Fake Transfer Service',
            client_id='fake_client_id',
            client_secret='fake_client_secret',
            redirect_uri='https://redirect_uri',
            supported_verticals=set(supported_verticals),
            state=None,
            verticals=set(verticals),
        )

    def scope_for_verticals(self, verticals):
        if ExtraScopeVertical in verticals:
            return SAMPLE_SCOPE | {'extra_scope'}
        return SAMPLE_SCOPE


@pytest.fixture
def blank_transfer_service(monkeypatch):
    return FakeTransferService([SocialPostingVertical], [])


def test_add_verticals_raises_exception(blank_transfer_service):
    with pytest.raises(InsufficientScopeException):
        blank_transfer_service.add_verticals([ExtraScopeVertical])


def test_set_verticals_raises_exception(blank_transfer_service):
    with pytest.raises(UnsupportedVerticalException):
        blank_transfer_service.verticals = [NewVertical]


@pytest.fixture
def mock_transfer_service():
    mock_transfer_service = FakeTransferService(
        [SocialPostingVertical, NewVertical, ExtraScopeVertical],
        [SocialPostingVertical],
    )
    mock_transfer_service.scope = SAMPLE_SCOPE
    return mock_transfer_service


def test_set_supported_verticals(mock_transfer_service):
    mock_transfer_service.verticals = [NewVertical]
    assert mock_transfer_service.verticals == {NewVertical}


def test_add_supported_verticals(mock_transfer_service):
    assert mock_transfer_service.add_verticals([NewVertical])
    assert mock_transfer_service.verticals == {SocialPostingVertical, NewVertical}


def test_add_unsupported_vertical_new_scope_required(
    monkeypatch, mock_transfer_service
):
    def _mock_scope_for_verticals(verticals):
        if ExtraScopeVertical in verticals:
            return {'new_scope'}
        return SAMPLE_SCOPE

    mock_transfer_service._oAuth2Session.access_token = 'access_token'
    monkeypatch.setattr(
        mock_transfer_service, 'scope_for_verticals', _mock_scope_for_verticals
    )
    assert not mock_transfer_service.add_verticals(
        [ExtraScopeVertical], should_reauth=True
    )
    assert not mock_transfer_service._oAuth2Session.access_token
    assert mock_transfer_service.scope == {'fake', 'scope', 'new_scope'}
    assert mock_transfer_service.verticals == {
        SocialPostingVertical,
        ExtraScopeVertical,
    }


def test_authorization_url(mock_transfer_service):
    auth_url, state = mock_transfer_service.authorization_url()

    auth_url_query = parse.urlsplit(auth_url).query
    auth_url_params = dict(parse.parse_qsl(auth_url_query))

    assert 'client_id' in auth_url_params
    assert auth_url_params['client_id'] == 'fake_client_id'
    assert 'redirect_uri' in auth_url_params
    assert auth_url_params['redirect_uri'] == 'https://redirect_uri'
    assert 'state' in auth_url_params
    assert auth_url_params['state'] == state


def test_fetch_token_raises_error(mock_transfer_service):
    with pytest.raises(ValueError):
        mock_transfer_service.fetch_token()


def test_fetch_token(
    mock_oauth2_session_request,
    mock_oauth2_session_response,
    mock_strava_transfer_service,
):
    mock_strava_transfer_service.fetch_token(code='123code123')
    mock_oauth2_session_request.assert_called_once()
    mock_oauth2_session_response.assert_called_once()


@pytest.mark.parametrize(
    ['path', 'base'],
    [
        ('test/path', SAMPLE_BASE_URL),
        ('test/path', f'{SAMPLE_BASE_URL}/'),
        ('/test/path', SAMPLE_BASE_URL),
        ('test/path', None),
        ('/test/path', None),
    ],
)
def test__build_resource_url(path, base, mock_transfer_service):
    resource_url = mock_transfer_service._build_resource_url(path, base)
    assert resource_url == 'https://api.example.com/v1/test/path'
