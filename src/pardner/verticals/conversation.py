from pydantic import Field

from pardner.verticals import BaseVertical
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


class ConversationVertical(BaseVertical):
    """
    The metadata related to a conversation where messages are exchanged between one
    or more people.
    """

    vertical_name: str = 'conversation'
    is_group_conversation: bool

    abstract: str | None = Field(
        description='A short summary, description, or bio.', default=None
    )
    associated_media: list[AssociatedMediaSubVertical] = []
    is_private: bool | None = None
    member_user_ids: list[str] = []
    members_count: int | None = None
    messages_count: int | None = None
    title: str | None = None
