from typing import Literal

from pydantic import Field

from pardner.verticals import BaseVertical
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


class SocialPostingVertical(BaseVertical):
    """
    A post on social media.
    """

    vertical_name: str = 'social_posting'

    abstract: str | None = Field(
        description='A short summary, description, or bio.', default=None
    )
    associated_media: list[AssociatedMediaSubVertical] = []
    interaction_count: int | None = None
    keywords: list[str] = []
    shared_content: list['SocialPostingVertical'] = []
    status: Literal['private', 'public', 'draft', 'restricted'] | None = None
    text: str | None = None
    title: str | None = None
