from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
import strawberry_django
from core.schema.common import permission_filtered_queryset
from core.schema.dataloaders import batch_load_users
from organization.models import Organization
from organization.models.organization import OrganizationMember
from strawberry.types import Info


@strawberry_django.type(Organization)
class OrganizationType:
    """An organization."""

    name: str
    slug: str
    description: Optional[str]
    website: Optional[str]
    guid: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)


# ---------------------------------------------------------------------------
# Employee connection types (for paginated employees query)
# ---------------------------------------------------------------------------

@strawberry.type
class EmployeeAvatarType:
    public_permanent_url: Optional[str]


@strawberry.type
class EmployeeProfileType:
    id: strawberry.ID
    display_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar: Optional[EmployeeAvatarType]


@strawberry.type
class EmployeeUserType:
    id: strawberry.ID
    first_name: str
    last_name: str
    email: str
    is_active: bool
    profile: Optional[EmployeeProfileType]


@strawberry.type
class EmployeeNode:
    id: strawberry.ID
    user: EmployeeUserType

    @classmethod
    def from_membership(cls, membership: OrganizationMember) -> EmployeeNode:
        user = membership.member
        profile = getattr(user, 'profile', None)
        avatar = None
        if profile and profile.avatar_id:
            from core.models import Upload
            upload = Upload.objects.filter(id=profile.avatar_id).first()
            if upload:
                avatar = EmployeeAvatarType(public_permanent_url=getattr(upload, 'public_permanent_url', None))

        profile_type = None
        if profile:
            profile_type = EmployeeProfileType(
                id=strawberry.ID(str(profile.pk)),
                display_name=profile.display_name,
                first_name=profile.first_name,
                last_name=profile.last_name,
                avatar=avatar,
            )

        return cls(
            id=strawberry.ID(str(membership.pk)),
            user=EmployeeUserType(
                id=strawberry.ID(str(user.pk)),
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                is_active=user.is_active,
                profile=profile_type,
            ),
        )


@strawberry.type
class EmployeeEdge:
    cursor: str
    node: EmployeeNode


@strawberry.type
class EmployeesPageInfo:
    has_next_page: bool


@strawberry.type
class EmployeesConnection:
    total_count: int
    edges: list[EmployeeEdge]
    page_info: EmployeesPageInfo


@strawberry_django.type(OrganizationMember)
class OrganizationMemberType:
    """A membership linking a user to an organization."""

    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    @strawberry_django.field
    def organization(self, info: Info) -> Optional[OrganizationType]:
        """Resolve organization from the per-request cache."""
        return info.context._organization_cache.get(self.organization_id)

    @strawberry_django.field
    async def member(self, info: Info) -> Optional[strawberry.scalars.JSON]:
        """Resolve member via the batch_load_users dataloader."""
        loader = info.context.get_loader('load_user_by_id', batch_load_users)
        return await loader.load(self.member_id)

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)
