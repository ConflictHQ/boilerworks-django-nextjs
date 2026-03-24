"""Assembled Strawberry GraphQL schema.

Merges Query and Mutation types from all apps into a single schema.
Disabled features are automatically excluded via config.features.
"""
import strawberry
from strawberry_django.optimizer import DjangoOptimizerExtension

from typing import Optional

from config.features import Feature, is_enabled

# ---------------------------------------------------------------------------
# Always-on imports (core infrastructure)
# ---------------------------------------------------------------------------
import core.schema.mutations as CoreMutations
import core_ui.schema as UiSchema
import organization.schema as OrganizationSchema
from core.schema.common import MutationResult
from core.schema.types.audit import AuditLogQuery
from core.schema.types.permission_analysis import PermissionAnalysisQuery
from core.schema.types.user import UserType


# ---------------------------------------------------------------------------
# Feature-gated imports
# ---------------------------------------------------------------------------
_query_bases = [PermissionAnalysisQuery, AuditLogQuery, UiSchema.Query, OrganizationSchema.Query]
_mutation_bases = [CoreMutations.Mutation, UiSchema.Mutation, OrganizationSchema.Mutation]

if is_enabled(Feature.FORMS):
    import forms.schema as FormsSchema
    from forms.schema.types import FormDefinitionType
    _query_bases.append(FormsSchema.Query)
    _mutation_bases.append(FormsSchema.Mutation)

if is_enabled(Feature.PUSH_NOTIFICATIONS):
    import pushnotif.schema as PushNotificationSchema
    _query_bases.append(PushNotificationSchema.Query)
    _mutation_bases.append(PushNotificationSchema.Mutation)

if is_enabled(Feature.WORKFLOWS):
    import workflows.schema as WorkflowsSchema
    _query_bases.append(WorkflowsSchema.Query)
    _mutation_bases.append(WorkflowsSchema.Mutation)


# ---------------------------------------------------------------------------
# Root Query
# ---------------------------------------------------------------------------

Query = strawberry.type(
    type('Query', tuple(_query_bases), {'__annotations__': {}}),
)


# ---------------------------------------------------------------------------
# Root Mutation
# ---------------------------------------------------------------------------

Mutation = strawberry.type(
    type('Mutation', tuple(_mutation_bases), {'__annotations__': {}}),
)


# ---------------------------------------------------------------------------
# Schema instance
# ---------------------------------------------------------------------------

from core.schema.audit import MutationAuditExtension
from core.schema.subscriptions import Subscription

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension, MutationAuditExtension],
)


# ---------------------------------------------------------------------------
# Auth schema (limited — login only, no auth required)
# ---------------------------------------------------------------------------

@strawberry.type
class AuthQuery:
    @strawberry.field
    def ok(self) -> str:
        return "ok"

    if is_enabled(Feature.FORMS):
        @strawberry.field(description="Get a public form by slug (no auth required).")
        def public_form(self, slug: str) -> Optional[FormDefinitionType]:
            from forms.models import FormDefinition, FormStatus
            return FormDefinition.objects.filter(
                slug=slug, status=FormStatus.PUBLISHED, is_public=True,
            ).first()


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

    if is_enabled(Feature.FORMS):
        @strawberry.mutation(description="Submit data to a public form (no auth required).")
        def submit_public_form(
            self, info: strawberry.types.Info, slug: str, payload: strawberry.scalars.JSON,
        ) -> MutationResult:
            from django.core.exceptions import ValidationError
            from graphql import GraphQLError

            from forms.models import FormDefinition, FormStatus, FormSubmission

            form = FormDefinition.objects.filter(
                slug=slug, status=FormStatus.PUBLISHED, is_public=True,
            ).first()
            if not form:
                raise GraphQLError(f'No public form found with slug "{slug}"')

            try:
                FormSubmission.submit(form, payload, user=None)
                return MutationResult.success()
            except ValidationError as e:
                raise GraphQLError(str(e))


schema_auth = strawberry.Schema(
    query=AuthQuery,
    mutation=AuthMutation,
)
