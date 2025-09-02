from pardner.verticals.conversation import ConversationVertical


class ConversationGroupVertical(ConversationVertical):
    """
    The metadata related to a conversation where messages are exchanged between one
    or more people.
    """

    vertical_name: str = 'conversation_group'
    is_group_conversation: bool = True
