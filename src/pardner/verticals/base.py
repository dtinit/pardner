from enum import StrEnum


class Vertical(StrEnum):
    """
    Represents the verticals, or categories of data, that are supported by `pardner`.
    Not all verticals are supported by every transfer service.
    """

    BlockedUser = 'blocked_user'
    ChatBot = 'chat_bot'
    ConversationDirect = 'conversation_direct'
    ConversationGroup = 'conversation_group'
    ConversationMessage = 'conversation_message'
    FeedPost = 'feed_post'
    PhysicalActivity = 'physical_activity'
