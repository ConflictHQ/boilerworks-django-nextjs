"""Superset mutations: guest tokens for embedded dashboards and dashboard config."""
from __future__ import annotations

import logging
from typing import Optional

import strawberry
from core.schema.common import MutationResult, ValidationError
from core.schema.mutations.base import restricted_serializer_mutate
from core.serializers.superset import SupersetDashboardSerializer
from graphql import GraphQLError
from strawberry.types import Info

logger = logging.getLogger(__name__)


@strawberry.type
class SupersetGuestTokenResult:
    ok: bool
    token: Optional[str] = None
    errors: list[ValidationError] = strawberry.field(default_factory=list)


def _error(message: str) -> SupersetGuestTokenResult:
    return SupersetGuestTokenResult(ok=False, errors=[ValidationError(field='dashboard', messages=[message])])


@strawberry.type
class SupersetMutations:

    @strawberry.mutation(description=(
        "Issue a short-lived Superset guest token for one embedded dashboard (by guid), "
        "with the dashboard's row-level security applied for the current user."
    ))
    def superset_guest_token(self, info: Info, dashboard: strawberry.ID) -> SupersetGuestTokenResult:
        from core.models import SupersetDashboard
        from core.utils.api.superset_rest_client import SupersetError, SupersetRestClient
        from django.core.exceptions import ValidationError as DjangoValidationError

        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError('Authentication required')
        SupersetDashboard.p('model').view.check(user)

        try:
            instance = SupersetDashboard.objects.filter(guid=dashboard, deleted_at__isnull=True).first()
        except DjangoValidationError:
            instance = None
        if instance is None:
            return _error('Dashboard not found.')

        try:
            token = SupersetRestClient().guest_token(instance.embedded_id, user, rls=instance.rls_rules(user))
        except SupersetError as error:
            logger.warning(f'Superset guest token for dashboard {instance.guid} failed: {error}')
            return _error('Analytics are unavailable right now.')
        return SupersetGuestTokenResult(ok=True, token=token)

    @strawberry.mutation(description="Create or update an embedded Superset dashboard via SupersetDashboardSerializer.")
    def superset_dashboard(self, info: Info, input: strawberry.scalars.JSON) -> MutationResult:
        from core.models import SupersetDashboard
        from django.core.exceptions import ValidationError as DjangoValidationError

        if not info.context.user.is_authenticated:
            raise GraphQLError('Authentication required')

        data = dict(input)
        guid = data.pop('guid', None)
        instance = None
        if guid:
            try:
                instance = SupersetDashboard.objects.filter(guid=guid, deleted_at__isnull=True).first()
            except DjangoValidationError:
                instance = None
            if instance is None:
                return MutationResult(ok=False, errors=[ValidationError(field='guid', messages=['Dashboard not found.'])])

        return restricted_serializer_mutate(SupersetDashboardSerializer, SupersetDashboard, info, data=data, instance=instance)
