from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from organization.models import Organization
from organization.models.organization import OrganizationMember
from organization.schema.types import (
    EmployeeEdge,
    EmployeeNode,
    EmployeesConnection,
    EmployeesPageInfo,
    OrganizationMemberType,
    OrganizationType,
)
from strawberry.types import Info


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

    @strawberry.field
    def employees(
        self,
        info: Info,
        first: Optional[int] = 10,
        offset: Optional[int] = 0,
        search: Optional[str] = None,
        show_deactivated: Optional[bool] = None,
        departments_department_name_icontains: Optional[str] = None,
        departments_position_name_icontains: Optional[str] = None,
    ) -> EmployeesConnection:
        """Paginated list of organization members (employees)."""
        from graphql import GraphQLError

        if not info.context.user.is_authenticated:
            raise GraphQLError('Authentication required')

        qs = OrganizationMember.objects.select_related('member', 'member__profile', 'organization').filter(
            deleted_at__isnull=True,
        )

        if show_deactivated is True:
            qs = qs.filter(is_active=False)
        elif show_deactivated is False:
            qs = qs.filter(is_active=True)

        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
                | Q(member__email__icontains=search)
                | Q(member__profile__display_name__icontains=search)
            )

        total_count = qs.count()
        page = qs.order_by('member__last_name', 'member__first_name')[offset:offset + first]

        edges = [
            EmployeeEdge(
                cursor=str(offset + i),
                node=EmployeeNode.from_membership(m),
            )
            for i, m in enumerate(page)
        ]

        return EmployeesConnection(
            total_count=total_count,
            edges=edges,
            page_info=EmployeesPageInfo(
                has_next_page=(offset + first) < total_count,
            ),
        )
