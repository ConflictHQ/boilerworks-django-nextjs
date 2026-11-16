from __future__ import annotations

import uuid
from typing import Optional

import strawberry
import strawberry_django
from core.models import SupersetDashboard
from django.conf import settings
from graphql import GraphQLError
from strawberry.types import Info


@strawberry_django.type(SupersetDashboard)
class SupersetDashboardType:
    """A Superset dashboard embedded through the Superset Embedded SDK."""
    guid: uuid.UUID
    embedded_id: uuid.UUID
    title: str
    description: Optional[str]
    order: int

    @strawberry_django.field(description="Superset origin the browser loads the embedded dashboard from.")
    def superset_domain(self) -> str:
        return settings.SUPERSET_PUBLIC_URL.rstrip('/')


@strawberry.type
class SupersetQuery:

    @strawberry.field(description="Embedded Superset dashboards the user can view, in display order.")
    def superset_dashboards(self, info: Info) -> list[SupersetDashboardType]:
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError('Authentication required')
        if not SupersetDashboard.p('model').view.check(user, False):
            return []
        return SupersetDashboard.objects.filter(deleted_at__isnull=True)
