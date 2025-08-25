from pardner.verticals import BaseVertical, ConversationVertical
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


class MessageVertical(BaseVertical):
    """
    A communication sent by ``creator_user_id`` and one or more
    recipients. This is related to a :class:`ConversationVertical`.
    """

    vertical_name: str = 'message'
    parent_conversation: ConversationVertical

    associated_media: list[AssociatedMediaSubVertical] = []
    text: str | None = None
