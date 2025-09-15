from typing import Literal

from pydantic import AnyHttpUrl

from pardner.verticals.sub_verticals.base import BaseSubVertical


class AssociatedMediaSubVertical(BaseSubVertical):
    """Holds the URL for the media attached to a parent vertical."""

    media_type: Literal['audio', 'image', 'video'] | None = None
    url: AnyHttpUrl | None = None
