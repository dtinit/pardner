from pydantic import AnyHttpUrl

from pardner.verticals.sub_verticals.base import BaseSubVertical


class AssociatedMediaSubVertical(BaseSubVertical):
    """Holds the URL for the media attached to a parent vertical."""

    audio_url: AnyHttpUrl | None = None
    image_url: AnyHttpUrl | None = None
    video_url: AnyHttpUrl | None = None
