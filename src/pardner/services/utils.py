from typing import Any


def scope_as_string(scopes: Any, delimiter: str = ' ') -> str | None:
    """
    Converts a sequence of individual scopes into a single scope string.

    :param scopes: a sequence of scopes as strings or a scope string.
    :param delimiter: the string used to separate individual scopes. Defaults to single space.

    :returns: a string containing all scopes.
    :raises :class:ValueError: if `scopes` is neither a string nor a sequence of strings
    """
    if isinstance(scopes, str) or scopes is None:
        return scopes
    elif isinstance(scopes, (set, tuple, list)):
        return delimiter.join([str(s) for s in sorted(scopes)])
    raise ValueError(f'Invalid scope ({scopes}), must be string, tuple, set, or list.')


def scope_as_set(scope: Any, delimiter: str = ' ') -> set[str]:
    """
    Splits a scope with potentially more than one scope into a set of scopes.

    :param scope: a string with one or more scopes.
    :param delimiter: the string used to separate individual scopes. Defaults to single space.

    :returns: a set of scopes.
    """
    if isinstance(scope, (tuple, list, set)):
        return {str(s) for s in scope}
    elif scope is None:
        return set()
    return set(scope.strip().split(delimiter))
