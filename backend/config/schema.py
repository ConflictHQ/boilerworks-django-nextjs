"""Assembled Strawberry GraphQL schema.

Merges Query and Mutation types from all apps into a single schema.
Replaces config/schema.py (Graphene).
"""
import strawberry
from strawberry_django.optimizer import DjangoOptimizerExtension

import core.schema.mutations as CoreMutations
import core_ui.schema as UiSchema
import forms.schema as FormsSchema
import organization.schema as OrganizationSchema
import pushnotif.schema as PushNotificationSchema
from typing import Optional

from core.schema.common import MutationResult
from core.schema.types.permission_analysis import PermissionAnalysisQuery
from core.schema.types.user import UserType
from forms.schema.types import FormDefinitionType


# ---------------------------------------------------------------------------
# Root Query — merges all app queries
# ---------------------------------------------------------------------------

@strawberry.type
class Query(
    PermissionAnalysisQuery,
    FormsSchema.Query,
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
    FormsSchema.Mutation,
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

    @strawberry.field(description="Get a public form by slug (no auth required).")
    def public_form(self, slug: str) -> Optional['FormDefinitionType']:
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

    @strawberry.mutation(description="Submit data to a public form (no auth required).")
    def submit_public_form(
        self, info: strawberry.types.Info, slug: str, payload: strawberry.scalars.JSON,
    ) -> 'MutationResult':
        from django.core.exceptions import ValidationError
        from graphql import GraphQLError

        from core.schema.common import MutationResult
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
