import logging

from django.db.models.expressions import Col
from django.db.models.sql.compiler import SQLAggregateCompiler


class NestedSQLAggregateCompiler(SQLAggregateCompiler):
    has_extra_select = False

    def as_sql(self, with_col_aliases=False):
        """
        Create the SQL for this query. Return the SQL string and list of
        parameters.
        """
        sql, params = [], []

        alias = hasattr(self.query, 'alias') and getattr(self.query, 'alias') or 'subquery'

        select_fields = []
        self.klass_info = {
            "model": self.query.model,
            "select_fields": select_fields
        }
        self.select = []
        column_index = -1
        if self.query.default_cols:
            for column in self.get_default_columns({}):
                column_index += 1
                ann_sql, ann_params = self.compile(column)
                ann_sql = f'{ann_sql}'
                ann_sql, ann_params = column.select_format(self, ann_sql, ann_params)
                sql.append(ann_sql)
                params.extend(ann_params)
                selected_col = column, (ann_sql, ann_params), None
                self.select.append(selected_col)
                select_fields.append(column_index)
        else:
            for column_alias, annotation in self.query.annotation_select.items():
                column_index += 1
                ann_sql, ann_params = self.compile(annotation)
                ann_sql = f'{ann_sql} as "{column_alias}"'
                ann_sql, ann_params = annotation.select_format(self, ann_sql, ann_params)
                sql.append(ann_sql)
                params.extend(ann_params)

                field = getattr(self.query.model, column_alias)
                if field and field.field:
                    col = Col(column_alias, target=field.field)
                    self.select.append((col, column_alias, ann_params))
                    select_fields.append(column_index)
                else:
                    logging.exception("eee")

        self.klass_info = {
            "model": self.query.model,
            "select_fields": select_fields,
        }

        self.col_count = len(self.query.annotation_select)

        sql = ", ".join(sql)
        params = tuple(params)

        inner_query_sql, inner_query_params = self.query.inner_query.get_compiler(
            using=self.using,
            connection=self.connection,
            elide_empty=self.elide_empty,
        ).as_sql(with_col_aliases=False)

        sql = "SELECT %s FROM (%s) %s" % (sql, inner_query_sql, alias)

        if self.query.group_by:
            group_by_columns = []
            for annotation in self.query.group_by:
                ann_sql, ann_params = self.compile(annotation)
                group_by_columns.append(ann_sql)
            group_by_str = ", ".join(group_by_columns)
            sql += " GROUP BY %s" % group_by_str

        params += inner_query_params

        return sql, params
