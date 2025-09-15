from typing import Literal

from pydantic import AnyHttpUrl, Field

from pardner.verticals.sub_verticals.base import BaseSubVertical


class AssociatedMediaSubVertical(BaseSubVertical):
    """Holds the URL for the media attached to a parent vertical."""

    media_type: Literal['audio', 'image', 'video'] | None = Field(
        description='If media type is unknown or not one of the types defined in this '
        'field, value is None.',
        default=None,
    )
    url: AnyHttpUrl | None = None
