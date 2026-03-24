"""Assembled Strawberry GraphQL schema.

Merges Query and Mutation types from all apps into a single schema.
Replaces config/schema.py (Graphene).
"""
import strawberry
from strawberry_django.optimizer import DjangoOptimizerExtension

import core.strawberry_schema.mutations as CoreMutations
import core_ui.strawberry_schema as UiSchema
import organization.strawberry_schema as OrganizationSchema
import pushnotif.strawberry_schema as PushNotificationSchema
from core.strawberry_schema.types.user import UserType


# ---------------------------------------------------------------------------
# Core queries (assembled from type modules)
# ---------------------------------------------------------------------------

@strawberry.type
class CoreQuery:
    pass  # Core queries will be added as fields here during Phase 6 full wiring


# ---------------------------------------------------------------------------
# Root Query — merges all app queries
# ---------------------------------------------------------------------------

@strawberry.type
class Query(
    UiSchema.Query,
    OrganizationSchema.Query,
    PushNotificationSchema.Query,
):
    pass


# ---------------------------------------------------------------------------
# Root Mutation — merges all app mutations
# ---------------------------------------------------------------------------

@strawberry.type
class Mutation(
    CoreMutations.Mutation,
    UiSchema.Mutation,
    OrganizationSchema.Mutation,
    PushNotificationSchema.Mutation,
):
    pass


# ---------------------------------------------------------------------------
# Schema instance
# ---------------------------------------------------------------------------

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension],
)


# ---------------------------------------------------------------------------
# Auth schema (limited — login only)
# ---------------------------------------------------------------------------

@strawberry.type
class AuthQuery:
    @strawberry.field
    def ok(self) -> str:
        return "ok"


@strawberry.type
class AuthMutation:
    @strawberry.mutation
    def login(self, info: strawberry.types.Info, username: str, password: str) -> UserType | None:
        from django.contrib.auth import authenticate, login
        user = authenticate(username=username, password=password)
        if user is not None:
            login(info.context.request, user)
            return user
        return None

    @strawberry.mutation
    def logout(self, info: strawberry.types.Info) -> bool:
        from django.contrib.auth import logout
        logout(info.context.request)
        return True


schema_auth = strawberry.Schema(
    query=AuthQuery,
    mutation=AuthMutation,
)
