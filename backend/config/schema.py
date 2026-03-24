import logging

# Import boilerworks schemas
import core.schema as CoreSchema
import core_ui.schema as UiSchema
import graphene
import organization.schema as OrganizationSchema
import pushnotif.schema as PushNotificationSchema
from graphql import specified_directives

logger = logging.getLogger(__name__)

# Base boilerworks query classes
_query_bases = [
    CoreSchema.Query,
    OrganizationSchema.Query,
    PushNotificationSchema.Query,
    UiSchema.Query,
]

# Base boilerworks mutation classes
_mutation_bases = [
    CoreSchema.Mutation,
    UiSchema.Mutation,
    OrganizationSchema.Mutation,
    PushNotificationSchema.Mutation,
]

# Domain apps register their schemas via ConfigMerger
# See config/config_merger.py for the dynamic schema loading mechanism


class Query(*_query_bases, graphene.ObjectType):
    pass


class Mutation(*_mutation_bases, graphene.ObjectType):
    pass


# noinspection PyTypeChecker
schema = graphene.Schema(query=Query, mutation=Mutation, directives=specified_directives)
