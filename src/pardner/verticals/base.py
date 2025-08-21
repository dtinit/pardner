from enum import StrEnum
from typing import Optional


class Vertical(StrEnum):
    """
    Represents the verticals, or categories of data, that are supported by this library.
    Not all verticals are supported by every transfer service.
    """

    BlockedUser = 'blocked_user'
    ChatBot = 'chat_bot'
    ConversationDirect = 'conversation_direct', 'conversations_direct'
    ConversationGroup = 'conversation_group', 'conversations_group'
    ConversationMessage = 'conversation_message'
    FeedPost = 'feed_post'
    PhysicalActivity = 'physical_activity', 'physical_activities'

    plural: str

    def __new__(cls, singular: str, plural: Optional[str] = None) -> 'Vertical':
        vertical_obj = str.__new__(cls, singular)
        vertical_obj._value_ = singular
        vertical_obj.plural = plural if plural else f'{singular}s'
        return vertical_obj
