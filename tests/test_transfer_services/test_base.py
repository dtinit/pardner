import pytest

from pardner.transfer_services.base import (
    BaseTransferService,
    InsufficientScopeException,
    UnsupportedVerticalException,
)
from pardner.verticals.base import Vertical

sample_scope = {'fake', 'scope'}


class FakeTransferService(BaseTransferService):
    def __init__(self, supported_verticals, verticals):
        super().__init__('', '', '')
        self._supported_verticals = set(supported_verticals)
        self._verticals = set(verticals)
        self._service_name = 'Fake Transfer Service'

    def scope_for_verticals(self, verticals):
        return sample_scope


@pytest.fixture
def mock_vertical(monkeypatch):
    Vertical.FAKE_VERTICAL = 'random_vertical'
    Vertical.NEW_VERTICAL = 'new_vertical'
    Vertical.NEW_VERTICAL_EXTRA_SCOPE = 'new_vertical_unsupported'


@pytest.fixture
def blank_transfer_service(monkeypatch):
    return FakeTransferService([], [])


def test_add_verticals_raises_exception(mock_vertical, blank_transfer_service):
    with pytest.raises(InsufficientScopeException):
        blank_transfer_service.add_verticals([Vertical.FAKE_VERTICAL])


def test_set_verticals_raises_exception(mock_vertical, blank_transfer_service):
    with pytest.raises(UnsupportedVerticalException):
        blank_transfer_service.verticals = [Vertical.FAKE_VERTICAL]


@pytest.fixture
def transfer_service(mock_vertical):
    mock_transfer_service = FakeTransferService(
        [Vertical.FAKE_VERTICAL, Vertical.NEW_VERTICAL, Vertical.NEW_VERTICAL_EXTRA_SCOPE],
        [Vertical.FAKE_VERTICAL],
    )
    mock_transfer_service.scope = sample_scope
    return mock_transfer_service


def test_set_supported_verticals(mock_vertical, transfer_service):
    transfer_service.verticals = [Vertical.NEW_VERTICAL]
    assert transfer_service.verticals == {Vertical.NEW_VERTICAL}


def test_add_supported_verticals(mock_vertical, transfer_service):
    assert transfer_service.add_verticals([Vertical.NEW_VERTICAL])
    assert transfer_service.verticals == {Vertical.FAKE_VERTICAL, Vertical.NEW_VERTICAL}


def test_add_unsupported_vertical_new_scope_required(monkeypatch, mock_vertical, transfer_service):
    def _mock_scope_for_verticals(verticals):
        if Vertical.NEW_VERTICAL_EXTRA_SCOPE in verticals:
            return {'new_scope'}
        return sample_scope

    transfer_service.access_token = 'access_token'
    monkeypatch.setattr(transfer_service, 'scope_for_verticals', _mock_scope_for_verticals)
    assert not transfer_service.add_verticals(
        [Vertical.NEW_VERTICAL_EXTRA_SCOPE], should_reauth=True
    )
    assert not transfer_service.access_token
    assert transfer_service.scope == {'fake', 'scope', 'new_scope'}
    assert transfer_service.verticals == {
        Vertical.FAKE_VERTICAL,
        Vertical.NEW_VERTICAL_EXTRA_SCOPE,
    }
