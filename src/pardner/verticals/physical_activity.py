from datetime import datetime

from pydantic import Field

from pardner.verticals.social_posting import SocialPostingVertical


class PhysicalActivityVertical(SocialPostingVertical):
    """
    A social posting that contains information related to a physical activity, such
    as running, swimming, or walking.
    """

    vertical_name: str = 'physical_activity'

    activity_type: str | None = Field(
        description='The type of physical activity, such as a hike.', default=None
    )
    distance: float | None = Field(description='In meters.', default=None)
    elevation_high: float | None = Field(description='In meters.', default=None)
    elevation_low: float | None = Field(description='In meters.', default=None)
    kilocalories: float | None = None
    max_speed: float | None = Field(description='In meters per second.', default=None)
    start_datetime: datetime | None = None
    start_latitude: float | None = None
    start_longitude: float | None = None
    end_datetime: datetime | None = None
    end_latitude: float | None = None
    end_longitude: float | None = None
