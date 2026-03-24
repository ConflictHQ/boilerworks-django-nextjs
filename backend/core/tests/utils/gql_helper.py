import json
import logging
import os
import re
from enum import Enum
from types import SimpleNamespace
from typing import Any, Union

from core.schema import schema as core_schema
from dateutil.parser import parse as date_parse
from django.conf import settings
from django.contrib.auth import get_user_model
from strawberry import Schema
from graphql import DocumentNode
from jsonpath_ng import DatumInContext, parse
from promise import Promise, is_thenable

logger = logging.getLogger(__name__)


class Queries:
    instance: 'Queries' = None

    def __init__(self):
        self.operations = {}

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = Queries()
        return cls.instance

    def add_document(self, document:  Union[DocumentNode, str]) -> 'Queries':
        doc = document
        if isinstance(doc, str):
            from graphql import parse
            doc = parse(doc)

        for df in doc.definitions:
            name = df.name.value
            if name in self.operations:
                logger.warning(f'Operation {name} already exists {self.operations[df.name.value]}')

            self.operations[df.name.value] = DocumentNode([df])
        return self

    def get_document(self, name) -> DocumentNode:
        return self.operations[name]

    def load(self, file) -> 'Queries':
        """
        if file extension is .js it will remove "export const ..." from the file
        :param file:
        :return:
        """
        f = os.path.join(settings.BASE_DIR, file)
        with open(f, 'r') as file:
            file_contents = file.read().strip()
            if file.name.endswith('.js'):
                file_contents = re.sub(r'export\sconst\s([\w.-]+)\s\=\sgql`', '', file_contents)
                file_contents = re.sub(r'^import\s+\{.*?;\n', '', file_contents)
                file_contents = file_contents.replace('`;', '')

            if len(file_contents):
                self.add_document(file_contents)

        return self


class Client:
    def __init__(self, schema: Schema, queries=Queries.get(), context=None, raise_errors=True):
        self.schema = schema
        self.queries: Queries = queries
        self.context = context or {}
        self.raise_errors = raise_errors

    def execute(self, doc_name, context=None, **kwargs) -> dict[str, Any]:
        context = context or self.context
        document = self.queries.get_document(doc_name)
        result = self._execute(document, context=context, variables=kwargs)

        if self.raise_errors and (result.errors or result.invalid):
            logger.debug(document)
            raise Exception(result.errors)

        return {
            'data': result.data,
            'errors': result.errors,
            'invalid': result.invalid,
        }

    def _execute(self, *args, **kwargs):
        executed = self.schema.execute(*args, **kwargs)
        if is_thenable(executed):
            return Promise.resolve(executed).then(self._format_result)

        return self._format_result(executed)

    def _format_result(self, result):
        return result


class JObject:
    """
    Result overrides __getattr__ to extract attributes from data
    """
    additional_sanitize_fields = 'referenceNumber',

    def __init__(self, gql_helper: 'GQLHelper' = None, data=None, source: 'JObject' = None, context=None):
        self.data = data
        self.gql_helper = gql_helper
        self.source = source
        self.context = context

    def to(self, result: 'JObject'):
        result.data = self.data
        result.gql_helper = self.gql_helper
        result.source = self
        result.jsonpath_result = self
        return result

    @property
    def gid(self):
        return self.first('id')

    def first(self, name):
        result = self.find(f'$..{name}')
        return result[0] if len(result) else None

    def all(self, name):
        return self.find(f'$..{name}')

    def _wrap(self, result, context=None):
        if isinstance(result, JObject):
            return result
        if isinstance(result, DatumInContext):
            return self._wrap(result.value, context=result)
        if isinstance(result, list):
            return [self._wrap(v, context) for v in result]
        if isinstance(result, dict):
            return JObject(self.gql_helper, result, source=self, context=context)

        return result

    def find(self, path, as_result=True):
        jsonpath_expr = parse(path)
        result = jsonpath_expr.find(self.data)
        if as_result:
            result = self._wrap(result)
        else:
            result = [r.value for r in result]
        return result

    @property
    def snapshot(self):
        return self.sanitize_result(self.data)

    @classmethod
    def is_date(cls, string):
        try:
            date_parse(string)
            return True
        except ValueError:
            return False

    @classmethod
    def sanitize_result(cls, data, key=None):
        if key and key in cls.additional_sanitize_fields:
            return f'**{key}**'

        if isinstance(data, dict):
            return {k: cls.sanitize_result(v, k) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_result(value) for value in data]
        elif isinstance(data, Enum):
            return str(data)
        elif isinstance(data, str) and cls.is_date(data):
            return '2022-01-01T00:00:00.000000+00:00'
        elif isinstance(data, str) and key == 'id':
            return '**id**'
        else:
            return data

    def __getattr__(self, item):
        value = self.data\
            .get('data', self.data)\
            .get(item)

        if value:
            return self._wrap(value)

        raise AttributeError(item)

    def __str__(self):
        return str(self.data)


class GQLHelper:
    """
    Generates Mock Data using graphql mutations
    graphql_files format is the same used by the next js client
    It is recommended to use this to generate data for tests
    """
    def __init__(self, schema=core_schema, graphql_files=()):
        self.queries = Queries()
        self.client = Client(schema, self.queries, raise_errors=False)

        for f in graphql_files:
            self.queries.load(f)

    @classmethod
    def context(cls, username=None, user=None):
        user = (
            user
            if user
            else get_user_model().objects.get(username=username if username else settings.API_SYSTEM_USER)
        )
        return SimpleNamespace(user=user, session={})

    def exec(self, mutation, context=None, **kwargs) -> JObject:
        result = self.client.execute(mutation,
                                     context=context if context else self.context(),
                                     **kwargs,
                                     )
        return JObject(self, result)

    def __getattr__(self, item):
        value = self.queries.operations.get(item)
        if value:
            def new_func(*args, **kwargs):
                out = self.exec(item, *args, **kwargs)
                return out

            return new_func

        ops = ', '.join(self.queries.operations.keys())
        raise AttributeError(f'Not found {item} - available op: {ops}')

    @classmethod
    def load_json(cls, path):
        with open(path, 'r') as f:
            return json.load(f)
