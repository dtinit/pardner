from typing import Any, Optional

from oauthlib.oauth2.rfc6749.utils import scope_to_list

from pardner.stateless import Scope


def scope_to_set(scope: Any) -> set[str]:
    return set(scope_to_list(scope)) if scope else set()


def has_sufficient_scope(
    old_scope: Optional[Scope], new_scope: Optional[Scope]
) -> bool:
    old_scope_set = scope_to_set(old_scope)
    new_scope_set = scope_to_set(new_scope)
    return new_scope_set.issubset(old_scope_set)
