from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
import strawberry_django
from strawberry.types import Info

from core.strawberry_schema.common import permission_filtered_queryset
from core.strawberry_schema.dataloaders import batch_load_users
from organization.models import Organization
from organization.models.organization import OrganizationMember


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
