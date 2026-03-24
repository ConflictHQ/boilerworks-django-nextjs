"""GraphQL introspection utilities for test automation.

Provides helpers for generating GraphQL queries from Strawberry type definitions.
"""
import dataclasses
from typing import Optional, Type

import graphql


default_exclude = ('version', 'created_at', 'updated_at', 'deleted_at')


@dataclasses.dataclass
class AutoGQLQuery:
    """Auto-generate GraphQL queries from a Strawberry type for testing."""
    gql_type: Type
    levels: int = 0
    variables: dict = dataclasses.field(default_factory=dict)
    query: str = None
    fields: list = dataclasses.field(default_factory=list)
    include: list = dataclasses.field(default_factory=list)
    exclude: list = dataclasses.field(default_factory=lambda: list(default_exclude))

    def __post_init__(self):
        if hasattr(self.gql_type, '__strawberry_definition__'):
            self.query = self._strawberry_type_to_query(self.gql_type, self.levels)
        else:
            self.query = '{ __typename }'

    def _strawberry_type_to_query(self, obj, levels: int = 0) -> Optional[str]:
        if levels < 0:
            return None

        definition = getattr(obj, '__strawberry_definition__', None)
        if not definition:
            return None

        query_fields = []
        for field in definition.fields:
            if field.name not in self.include:
                if field.name in self.exclude or (self.fields and field.name not in self.fields):
                    continue
            query_fields.append(field.name)

        if not query_fields:
            return None

        fields_str = '\n'.join(query_fields)
        return f'{{\n{fields_str}\n}}'

    @classmethod
    def beautify(cls, query):
        ast = graphql.parse(query)
        return graphql.print_ast(ast)

    def to_query(self, name, return_type=None, filter_query: dict = None, close_query=True):
        filter_str = ''
        if filter_query:
            filter_str = f'({", ".join([f"{k}: {v}" for k, v in filter_query.items()])})'

        sub_q = f'{name} {filter_str} {self.query}'

        if close_query:
            return self.beautify(f'query q{name.capitalize()} {{\n{sub_q}\n}}')
        return self.beautify(sub_q)
