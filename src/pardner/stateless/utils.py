from typing import Any, Optional

from oauthlib.oauth2.rfc6749.utils import scope_to_list

from pardner.stateless import Scope


def scope_to_set(scope: Any) -> set[str]:
    """
    Splits `scope` into each individual scope and puts the values in a set of strings.
    Leverages OAuthlib library helpers.

    :param scope: the string or sequence/iterable of objects that will be converted to
    a set of strings.

    :returns: a set of strings where each string is an individual scope.
    """
    return set(scope_to_list(scope)) if scope else set()


def has_sufficient_scope(
    old_scope: Optional[Scope], new_scope: Optional[Scope]
) -> bool:
    """
    Given an old scope and a new scope, determines if the new scope has scopes that are
    not in the original `old_scope`.

    :param old_scope: zero or more scopes.
    :param new_scope: zero or more scopes.

    :returns: True if `new_scope` has no new scopes and False otherwise.
    """
    old_scope_set = scope_to_set(old_scope)
    new_scope_set = scope_to_set(new_scope)
    return new_scope_set.issubset(old_scope_set)
