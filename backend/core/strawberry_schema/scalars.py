import datetime
from typing import NewType

import strawberry
from graphql import GraphQLError

TimeDeltaSeconds = NewType("TimeDeltaSeconds", float)


@strawberry.scalar(
    TimeDeltaSeconds,
    name="TimeDelta",
    description="A timedelta value represented as total seconds.",
)
class TimeDelta:
    @staticmethod
    def serialize(value: datetime.timedelta) -> float:
        if not isinstance(value, datetime.timedelta):
            raise GraphQLError(f"TimeDelta cannot represent value: {repr(value)}")
        return value.total_seconds()

    @staticmethod
    def parse_value(value: int | float) -> datetime.timedelta:
        if isinstance(value, datetime.timedelta):
            return value
        if not isinstance(value, (int, float)):
            raise GraphQLError(f"TimeDelta seconds value must be numeric: {repr(value)}")
        return datetime.timedelta(seconds=value)
