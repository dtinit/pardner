import pytest

from pardner.services.utils import scope_as_set, scope_as_string


@pytest.mark.parametrize(
    ['scopes', 'delimiter', 'expected', 'expected_with_delimiter'],
    [
        ({'first', 'second'}, '+', 'first second', 'first+second'),
        ('first+second', '+', 'first+second', 'first+second'),
    ],
)
def test_scope_as_string(scopes, delimiter, expected, expected_with_delimiter):
    assert scope_as_string(scopes) == expected
    assert scope_as_string(scopes, delimiter) == expected_with_delimiter


def test_scope_as_string_raises_error():
    with pytest.raises(ValueError):
        scope_as_string(100)


@pytest.mark.parametrize(
    ['scope', 'delimiter', 'expected', 'expected_with_delimiter'],
    [
        ('first+second', '+', {'first+second'}, {'first', 'second'}),
        ({'first', 'second'}, '+', {'first', 'second'}, {'first', 'second'}),
        ([], '--', set(), set()),
        (None, '--', set(), set()),
    ],
)
def test_scope_as_set(scope, delimiter, expected, expected_with_delimiter):
    assert scope_as_set(scope) == expected
    assert scope_as_set(scope, delimiter) == expected_with_delimiter
