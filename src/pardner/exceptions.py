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
