
from core.schema import schema as core_schema
from core.tests.utils.gql_helper import GQLHelper, JObject


class CoreGQL(GQLHelper):
    _instance = None

    def __init__(self, schema=core_schema):
        super().__init__(schema, graphql_files=('../frontend/graphql/mutations.js',
                                                '../frontend/graphql/queries.js',))

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def create_user(self, user_data, context=None) -> JObject:
        return self.exec('userMutation', context, **user_data)

    def get_assignable_permissions(self, module, assignable) -> JObject:
        return self.assignablePermissions(module=module, assignable=assignable)
