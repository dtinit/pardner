from typing import Any

from pardner.verticals import Vertical


class InsufficientScopeException(Exception):
    def __init__(self, *unsupported_verticals: Vertical, service_name: str) -> None:
        combined_verticals = ', '.join(
            [str(vertical) for vertical in unsupported_verticals]
        )
        super().__init__(
            f'Cannot add {combined_verticals} to {service_name} with current scope.'
        )


class UnsupportedVerticalException(Exception):
    def __init__(self, *unsupported_verticals: Vertical, service_name: str) -> None:
        combined_verticals = ', '.join(
            [str(vertical) for vertical in unsupported_verticals]
        )
        is_more_than_one_vertical = len(unsupported_verticals) > 1
        super().__init__(
            f'Cannot fetch {combined_verticals} from {service_name} because '
            f'{"they are" if is_more_than_one_vertical else "it is"} not supported.'
        )


class UnsupportedRequestException(Exception):
    def __init__(self, service_name: str, message: str):
        super().__init__(f'Cannot fetch data from {service_name}: {message}')


class TumblrAPIError(Exception):
    """
    Raised when the Tumblr API returns a non-OK HTTP status or a success response
    whose payload is missing expected structure
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        raw_response: Any = None,
    ) -> None:
        detail = f'Tumblr API error: {message}'
        if status_code is not None:
            detail += f' (HTTP {status_code})'
        super().__init__(detail)
        self.status_code = status_code
        self.raw_response = raw_response
