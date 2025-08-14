from enum import StrEnum


class Vertical(StrEnum):
    """
    Represents the verticals, or categories of data, that are supported by `pardner`.
    Not all verticals are supported by every transfer service.
    """

    FeedPost = 'feed_post'
    PhysicalActivity = 'physical_activity'
