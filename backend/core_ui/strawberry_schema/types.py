from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
import strawberry_django
from strawberry.types import Info

from core.strawberry_schema.common import permission_filtered_queryset
from core_ui.models import Component


@strawberry_django.filter(Component)
class ComponentFilter:
    slug: Optional[str] = strawberry.UNSET

    def filter_slug(self, queryset, info: Info, value: str):
        qs = queryset.filter(slug=value)
        if qs.exists():
            return qs

        component = Component.objects.filter(slug=value).first()
        if component:
            from core_logs.models import PermissionAccessLog
            PermissionAccessLog.log_denied(
                info.context.user,
                component.permissions.filter(codename__startswith='view_').first(),
                msg=f'User does not have access to component with slug "{value}"',
            )
            return queryset.none()

        from graphql import GraphQLError
        raise GraphQLError(f'Component with slug "{value}" does not exist')


@strawberry_django.type(Component, exclude=['components', 'permissions', 'parents'])
class ComponentType:
    """A UI component with permissions-based visibility."""

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)

    @strawberry.field
    def children(self, info: Info) -> list[ComponentType]:
        """Child components filtered by the user's group permissions."""
        all_children = Component.objects.filter(parents=self)
        permitted = all_children.filter(
            pk__in=Component.objects.filter(
                permissions__group__in=info.context.user.groups.all()
            )
        )

        denied_slugs = list(
            all_children.exclude(pk__in=permitted).values_list('slug', flat=True)
        )
        if denied_slugs:
            from core_logs.models import PermissionAccessLog
            PermissionAccessLog.log_denied(
                info.context.user,
                msg=f'User does not have access to components: "{", ".join(denied_slugs)}"',
            )

        return permitted.order_by('through_parents__order')
