import datetime

import graphene
import graphql


class TimeDeltaScalar(graphene.Scalar):
    """Custom scalar for representing timedelta in GraphQL."""

    @staticmethod
    def serialize(date):
        if not isinstance(date, datetime.timedelta):
            raise graphql.GraphQLError(f"Date cannot represent value: {repr(date)}")
        return date.total_seconds()

    @classmethod
    def parse_literal(cls, node, _variables=None):
        if not isinstance(node, graphql.IntValueNode):
            raise graphql.GraphQLError(
                f"Date cannot represent non-string value: {graphql.print_ast(node)}"
            )
        return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        if isinstance(value, datetime.timedelta):
            return value

        if not isinstance(value, int):
            raise graphql.GraphQLError(f"Seconds value must be int: {repr(value)}")

        return datetime.timedelta(seconds=value)
