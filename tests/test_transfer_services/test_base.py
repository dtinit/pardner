from urllib import parse

import pytest

from pardner.services import (
    BaseTransferService,
    InsufficientScopeException,
    UnsupportedVerticalException,
)
from pardner.verticals import Vertical

sample_scope = {'fake', 'scope'}


class FakeTransferService(BaseTransferService):
    _authorization_url = 'https://auth_url'
    _token_url = 'https://token_url'

    def __init__(self, supported_verticals, verticals):
        super().__init__(
            'Fake Transfer Service',
            'fake_client_id',
            'fake_client_secret',
            'https://redirect_uri',
            set(supported_verticals),
            None,
            set(verticals),
        )

    def scope_for_verticals(self, verticals):
        if Vertical.NEW_VERTICAL_EXTRA_SCOPE in verticals:
            return sample_scope | {'extra_scope'}
        return sample_scope


@pytest.fixture
def blank_transfer_service(monkeypatch):
    return FakeTransferService([Vertical.FeedPost], [])


def test_add_verticals_raises_exception(mock_vertical, blank_transfer_service):
    with pytest.raises(InsufficientScopeException):
        blank_transfer_service.add_verticals([Vertical.NEW_VERTICAL_EXTRA_SCOPE])


def test_set_verticals_raises_exception(mock_vertical, blank_transfer_service):
    with pytest.raises(UnsupportedVerticalException):
        blank_transfer_service.verticals = [Vertical.NEW_VERTICAL]


@pytest.fixture
def mock_transfer_service(mock_vertical):
    mock_transfer_service = FakeTransferService(
        [Vertical.FeedPost, Vertical.NEW_VERTICAL, Vertical.NEW_VERTICAL_EXTRA_SCOPE],
        [Vertical.FeedPost],
    )
    mock_transfer_service.scope = sample_scope
    return mock_transfer_service


def test_set_supported_verticals(mock_vertical, mock_transfer_service):
    mock_transfer_service.verticals = [Vertical.NEW_VERTICAL]
    assert mock_transfer_service.verticals == {Vertical.NEW_VERTICAL}


def test_add_supported_verticals(mock_vertical, mock_transfer_service):
    assert mock_transfer_service.add_verticals([Vertical.NEW_VERTICAL])
    assert mock_transfer_service.verticals == {Vertical.FeedPost, Vertical.NEW_VERTICAL}


def test_add_unsupported_vertical_new_scope_required(
    monkeypatch, mock_vertical, mock_transfer_service
):
    def _mock_scope_for_verticals(verticals):
        if Vertical.NEW_VERTICAL_EXTRA_SCOPE in verticals:
            return {'new_scope'}
        return sample_scope

    mock_transfer_service._oAuth2Session.access_token = 'access_token'
    monkeypatch.setattr(
        mock_transfer_service, 'scope_for_verticals', _mock_scope_for_verticals
    )
    assert not mock_transfer_service.add_verticals(
        [Vertical.NEW_VERTICAL_EXTRA_SCOPE], should_reauth=True
    )
    assert not mock_transfer_service._oAuth2Session.access_token
    assert mock_transfer_service.scope == {'fake', 'scope', 'new_scope'}
    assert mock_transfer_service.verticals == {
        Vertical.FeedPost,
        Vertical.NEW_VERTICAL_EXTRA_SCOPE,
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


def test_fetch_token(mock_oAuth2Session, mock_strava_transfer_service):
    [mock_request, mock_response] = mock_oAuth2Session
    mock_strava_transfer_service.fetch_token(code='123code123')
    mock_request.assert_called_once()
    mock_response.assert_called_once()
