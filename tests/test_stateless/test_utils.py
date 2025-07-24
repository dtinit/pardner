import pytest

from pardner.stateless.utils import has_sufficient_scope, scope_to_set

expected_set = {'scope1', 'scope2', 'scope3'}


@pytest.mark.parametrize(
    ['scopes', 'expected'],
    [
        ('scope1 scope2 scope3', expected_set),
        (['scope1', 'scope2', 'scope3'], expected_set),
        (['scope2', 'scope1', 'scope3'], expected_set),
        (('scope1', 'scope2', 'scope3'), expected_set),
        (['scope1', 'scope2', 'scope3'], expected_set),
        ({'scope1', 'scope2', 'scope3'}, expected_set),
    ],
)
def test_scope_to_set(scopes, expected):
    assert scope_to_set(scopes) == expected


@pytest.mark.parametrize(
    ['old_scope', 'new_scope', 'expected'],
    [
        ('scope1 scope2 scope3', 'scope1 scope2 scope3', True),
        ('scope1 scope2 scope3', ['scope1', 'scope2'], True),
        ({'scope1', 'scope2'}, 'scope1 scope2 scope3', False),
        ('', 'scope1 scope2 scope3', False),
    ],
)
def test_has_sufficient_scope(old_scope, new_scope, expected):
    assert has_sufficient_scope(old_scope, new_scope) == expected
