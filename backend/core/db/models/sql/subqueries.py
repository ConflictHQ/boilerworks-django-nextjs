from django.db import connections
from django.db.models.sql import Query
from django.db.models.sql.subqueries import AggregateQuery

from .compiler import NestedSQLAggregateCompiler

__all__ = [
    "NestedAggregateQuery",
]


class NestedAggregateQuery(AggregateQuery):

    def __init__(self, alias: str, model, inner_query: Query):
        inner_query.sql_with_params()  # Force query rendering
        super().__init__(model, inner_query)
        self.alias = alias
        self.table_name = alias
        self.default_cols = False
        self.alias_map[alias] = inner_query.alias_map[inner_query.base_table]
        self.alias_refcount[alias] = 1
        self.filtered_relation = None

    def get_compiler(self, using=None, connection=None, elide_empty=True):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        # original = connection.ops.compiler(self.compiler)
        return NestedSQLAggregateCompiler(
            self, connection, using, elide_empty
        )
