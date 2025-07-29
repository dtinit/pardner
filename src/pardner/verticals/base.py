from enum import StrEnum


class Vertical(StrEnum):
    """
    Represents the verticals, or categories of data, that are supported by `pardner`.
    Not all verticals are supported by every transfer service.
    """

    ExerciseAction = 'exercise_action'
    FeedPost = 'feed_post'
    Follower = 'follower'
    Profile = 'profile'
