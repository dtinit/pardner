from pardner.verticals import BaseVertical


class BlockedUserVertical(BaseVertical):
    """An instance of a user blocked by ``creator_user_id``."""

    vertical_name: str = 'blocked_user'
    blocked_user_id: str
