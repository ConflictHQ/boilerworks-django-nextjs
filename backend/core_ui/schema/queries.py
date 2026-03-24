from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from core_ui.models import Component
from core_ui.schema.types import ComponentFilter, ComponentType


@strawberry.type
class Query:

    @strawberry.field
    def components(self, info: Info) -> list[ComponentType]:
        return Component.objects.with_view_permission_info(info)

    @strawberry_django.field
    def component(self, info: Info, slug: str) -> Optional[ComponentType]:
        return (
            Component.objects
            .with_view_permission_info(info)
            .filter(slug=slug)
            .first()
        )
