from typing import Any

from django.core.exceptions import FullResultSet
from django.db.models import Field
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import WhereNode

from .subqueries import NestedAggregateQuery


class DateBetweenJoin:

    def __init__(self, date: Field, lower_bound: Field, upper_bound: Field):
        self.date: Field = date.field
        self.lower_bound: Field = lower_bound.field
        self.upper_bound: Field = upper_bound.field

    def get_joining_fields(self, *args, **kwargs):
        return {}

    def get_extra_restriction(self, table_alias: str, parent_alias: str):
        cond = WhereNode()
        cond.add(
            self.date.get_lookup("range")(
                self.date.get_col(table_alias),
                (
                    self.lower_bound.get_col(parent_alias),
                    self.upper_bound.get_col(parent_alias),
                ),
            ),
            "AND"
        )
        return cond


class NestedQueryJoin(Join):
    """
    Used by sql.Query and sql.SQLCompiler to generate JOIN clauses into the
    FROM entry. For example, the SQL generated could be
        LEFT OUTER JOIN "sometable" T1
        ON ("othertable"."sometable_id" = "sometable"."id")

    This class is primarily used in Query.alias_map. All entries in alias_map
    must be Join compatible by providing the following attributes and methods:
        - table_name (string)
        - table_alias (possible alias for the table, can be None)
        - join_type (can be None for those entries that aren't joined from
          anything)
        - parent_alias (which table is this join's parent, can be None similarly
          to join_type)
        - as_sql()
        - relabeled_clone()
    """

    def __init__(
            self,
            aggregation_query: NestedAggregateQuery,
            table_name: str,
            parent_alias: str,
            table_alias: str,
            join_type: str,
            join_field: Any,
            nullable: bool,
            filtered_relation=None,
    ):
        super().__init__(
            table_name=table_name,
            parent_alias=parent_alias,
            table_alias=table_alias,
            join_type=join_type,
            join_field=join_field,
            nullable=nullable,
            filtered_relation=filtered_relation
        )
        self.aggregation_query = aggregation_query

    def as_sql(self, compiler, connection):
        """
        Generate the full
           LEFT OUTER JOIN sometable ON sometable.somecol = othertable.othercol, params
        clause for this join.
        """
        join_conditions = []
        params = []
        qn = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
        # Add a join condition for each pair of joining columns.
        # RemovedInDjango60Warning: when the depraction ends, replace with:
        # for lhs, rhs in self.join_field:
        join_fields = self.join_fields or self.join_cols
        for lhs, rhs in join_fields:
            if isinstance(lhs, str):
                # RemovedInDjango60Warning: when the depraction ends, remove
                # the branch for strings.
                lhs_full_name = "%s.%s" % (qn(self.parent_alias), qn2(lhs))
                rhs_full_name = "%s.%s" % (qn(self.table_alias), qn2(rhs))
            else:
                lhs, rhs = connection.ops.prepare_join_on_clause(
                    self.parent_alias, lhs, self.table_alias, rhs
                )
                lhs_sql, lhs_params = compiler.compile(lhs)
                lhs_full_name = lhs_sql % lhs_params
                rhs_sql, rhs_params = compiler.compile(rhs)
                rhs_full_name = rhs_sql % rhs_params
            join_conditions.append(f"{lhs_full_name} = {rhs_full_name}")

        # Add a single condition inside parentheses for whatever
        # get_extra_restriction() returns.
        extra_cond = self.join_field.get_extra_restriction(
            self.table_alias, self.parent_alias
        )
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            join_conditions.append("(%s)" % extra_sql)
            params.extend(extra_params)
        if self.filtered_relation:
            try:
                extra_sql, extra_params = compiler.compile(self.filtered_relation)
            except FullResultSet:
                pass
            else:
                join_conditions.append("(%s)" % extra_sql)
                params.extend(extra_params)
        if not join_conditions:
            # This might be a rel on the other end of an actual declared field.
            declared_field = getattr(self.join_field, "field", self.join_field)
            raise ValueError(
                "Join generated an empty ON clause. %s did not yield either "
                "joining columns or extra restrictions." % declared_field.__class__
            )
        on_clause_sql = " AND ".join(join_conditions)
        alias_str, sub_params = self.aggregation_query.get_compiler(
            using=compiler.using,
            connection=connection,
        ).as_sql(with_col_aliases=True)
        params.extend(sub_params)
        sql = "%s (%s) %s ON (%s)" % (
            self.join_type,
            alias_str,
            qn(self.table_name),
            on_clause_sql,
        )
        return sql, params
