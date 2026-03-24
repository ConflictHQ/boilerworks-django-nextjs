from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from strawberry.types import Info

from core.schema.common import permission_filtered_queryset


# ---------------------------------------------------------------------------
# Non-model types (introspection of the permission system)
# ---------------------------------------------------------------------------

@strawberry.type
class FieldPermissionType:
    """CRUD permission flags for a single field."""
    name: str

    @strawberry.field
    def add(self, info: Info) -> bool:
        return self.can_add(info.context.user)

    @strawberry.field
    def view(self, info: Info) -> bool:
        return self.can_view(info.context.user)

    @strawberry.field
    def change(self, info: Info) -> bool:
        return self.can_change(info.context.user)

    @strawberry.field
    def delete(self, info: Info) -> bool:
        return self.can_delete(info.context.user)


@strawberry.type
class FieldType:
    """A Django model field with permission metadata."""
    field_type: str
    name: str
    verbose_name: str
    permissions: Optional[FieldPermissionType]


@strawberry.type
class ModelType:
    """A Django model with its permission and field metadata."""
    model_name: str
    verbose_name: str
    verbose_name_plural: str
    permissions: list[FieldPermissionType]
    fields: list[FieldType]


# ---------------------------------------------------------------------------
# Django-model-backed types
# ---------------------------------------------------------------------------

@strawberry_django.type(Group)
class GroupType:

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)


@strawberry_django.type(Permission)
class PermissionType:
    pass


@strawberry_django.type(ContentType)
class ContentTypeType:
    pass
