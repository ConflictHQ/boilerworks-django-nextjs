import dataclasses
from typing import Optional, Type

import graphql
from core.utils.graphene_utils import GrapheneUtils
from graphene import Dynamic, Field, List, NonNull
from graphene.types.objecttype import ObjectTypeMeta
from graphene.utils.subclass_with_meta import SubclassWithMeta_Meta
from graphene_django import DjangoConnectionField, DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

default_exclude = 'version', 'created_at', 'updated_at', 'deleted_at'


@dataclasses.dataclass
class AutoGQLQuery:
    gql_type: Type[DjangoObjectType]
    levels: int = 0
    variables: dict = dataclasses.field(default_factory=dict)
    query: str = None
    fields: list = dataclasses.field(default_factory=list)
    include: list = dataclasses.field(default_factory=list)
    exclude: list = dataclasses.field(default_factory=lambda: default_exclude)

    def __post_init__(self):
        self.query = self._type_object_to_query(self.gql_type, self.levels)

    def _type_object_to_query(self, obj, levels: int = 0) -> Optional[str]:
        if levels < 0:
            return None

        query = ''
        for field_name, field in obj._meta.fields.items():
            if field_name not in self.include:
                if field_name in self.exclude or self.fields and field_name not in self.fields:
                    continue

            field_type = field
            if isinstance(field, Dynamic):
                field_type = field.get_type()

            str_field = self._field_to_query(field_name, field_type, levels + 1 if field_name in self.include else 0)
            if str_field:
                query += f"{str_field}\n"

        query = f"{{\n{query}\n}}"
        return query

    def _field_to_query(self, field_name, field: Field, levels: int = 0) -> Optional[str]:
        try:
            if field is None:
                return None
            field_name = GrapheneUtils.to_camel_case(field_name)
            node = self._extract(lambda: field.type.of_type.Edge.node) or self._extract(lambda: field.type.Edge.node)
            if node:
                sub_query = self._connection_field_to_query(field_name, node, levels)
            elif isinstance(field.type, List):
                sub_query = self._type_object_to_query(field.type.of_type, levels)
                sub_query = f'{sub_query}\n' if sub_query else None
            else:
                of_type = field.type.of_type if isinstance(field.type, NonNull) else field.type
                if isinstance(of_type, SubclassWithMeta_Meta):
                    is_complex_field = (isinstance(of_type, ObjectTypeMeta) or
                                        isinstance(of_type, ObjectTypeMeta))
                else:
                    is_complex_field = isinstance(of_type, ObjectTypeMeta) or \
                                       isinstance(of_type, ObjectTypeMeta)
                if not is_complex_field:
                    return f'{field_name}'

                sub_query = self._type_object_to_query(of_type, levels - 1)
            return f'{field_name} {sub_query}' if sub_query else None
        except Exception as e:
            print(f'Error on field {field_name}: {e}')
            return None

    def _extract(self, lambda_func, *args, **kwargs):
        try:
            return lambda_func(*args, **kwargs)
        except Exception:
            return None

    def _connection_field_to_query(self, field_name, node, levels: int = 0) -> Optional[str]:
        node_query = self._type_object_to_query(node.type, levels - 1)
        sub_query = f"""{{
            edges {{
            node
                {node_query}
            }}
        }}"""
        return sub_query if node_query else None

    @classmethod
    def beautify(cls, query):
        ast = graphql.parse(query)
        return graphql.print_ast(ast)

    def to_query(self, name, return_type: Type[DjangoConnectionField] | DjangoObjectType, filter_query: dict = None, close_query=True):
        filter_str = ''
        if filter_query:
            filter_str = f'({", ".join([f"{k}: {v}" for k, v in filter_query.items()])})'

        if return_type == DjangoFilterConnectionField:
            sub_q = f'{name} {filter_str} {{\nedges {{\nnode {self.query}\n}}\n\n}}'
        else:
            sub_q = f'{name} {filter_str} {self.query}'

        if close_query:
            return self.beautify(f'query q{name.capitalize()} {{\n{sub_q}\n}}')
        return self.beautify(sub_q)
