from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from core_ui.models import Component
from core_ui.schema.types import ComponentType


@strawberry.type
class ComponentTreeNode:
    """A component with its nested children, for tree rendering."""
    name: str
    slug: str
    path: Optional[str]
    icon: Optional[str]
    is_active: bool
    properties: strawberry.scalars.JSON
    children: list[ComponentTreeNode]


def _build_tree(component: Component, info: Info, depth: int = 0, max_depth: int = 10) -> ComponentTreeNode:
    """Recursively build component tree."""
    children = []
    if depth < max_depth:
        for child in component.components.order_by('through_parents__order'):
            children.append(_build_tree(child, info, depth + 1, max_depth))

    return ComponentTreeNode(
        name=component.name,
        slug=component.slug,
        path=component.path,
        icon=component.icon,
        is_active=component.is_active,
        properties=component.properties or {},
        children=children,
    )


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

    @strawberry.field(description="Get a component tree starting from a root slug.")
    def component_tree(self, info: Info, root_slug: str) -> Optional[ComponentTreeNode]:
        root = Component.objects.filter(slug=root_slug).first()
        if not root:
            return None
        return _build_tree(root, info)

    @strawberry.field(description="Export component configuration as JSON (for seeding/sharing).")
    def component_export(self, info: Info, slugs: list[str]) -> strawberry.scalars.JSON:
        components = Component.objects.filter(slug__in=slugs)
        export = []
        for comp in components:
            export.append({
                'name': comp.name,
                'slug': comp.slug,
                'description': comp.description,
                'path': comp.path,
                'icon': comp.icon,
                'is_active': comp.is_active,
                'properties': comp.properties,
                'children': [
                    {'slug': child.slug, 'order': rel.order}
                    for rel in comp.through_children.select_related('child').all()
                    for child in [rel.child]
                ],
            })
        return export
