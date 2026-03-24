from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from organization.models import Organization
from organization.models.organization import OrganizationMember
from organization.schema.types import OrganizationMemberType, OrganizationType


@strawberry.type
class Query:

    @strawberry_django.field
    def organization(self, info: Info, id: strawberry.ID) -> Optional[OrganizationType]:
        """Fetch a single organization by ID, using the per-request cache."""
        from core.schema.common import GlobalIDUtils

        pk = GlobalIDUtils.get_pk_flexible(id, expected_type='OrganizationType')
        if pk is None:
            return None
        return info.context._organization_cache.get(int(pk))

    @strawberry.field
    def organizations(self, info: Info, query: Optional[str] = None) -> list[OrganizationType]:
        """List organizations, optionally filtered by a search query."""
        qs = Organization.objects.all()
        if query:
            terms = [q for q in query.split(' ') if q]
            for term in terms:
                qs = qs.filter(search__icontains=term)
        return qs

    @strawberry.field
    def members(self, info: Info) -> list[OrganizationMemberType]:
        """List organization members."""
        return OrganizationMember.objects.all()
