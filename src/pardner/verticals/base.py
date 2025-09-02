from abc import ABC
from datetime import datetime
from typing import Type

from pydantic import AnyHttpUrl, BaseModel, Field


class BaseVertical(BaseModel, ABC):
    """
    Base class for all verticals, except sub-verticals. Represents the verticals, or
    categories of data, that are supported by this library. Not all verticals are
    supported by every transfer service.
    """

    id: str
    creator_user_id: str
    service: str = Field(
        description='The name of the service the data was pulled from.'
    )
    vertical_name: str = Field(description='The name of the vertical, in snake case.')

    created_at: datetime | None = None
    url: AnyHttpUrl | None = None

    def __str__(self):
        return self.vertical_name


Vertical = Type[BaseVertical]
