from pardner.verticals.conversation import ConversationVertical


class ConversationDirectVertical(ConversationVertical):
    """
    The metadata related to a conversation where messages are exchanged between one
    or more people.
    """

    vertical_name: str = 'conversation_direct'

    is_group_conversation: bool = False
    members_count: int = 2
