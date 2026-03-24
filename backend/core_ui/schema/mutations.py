from __future__ import annotations

from typing import Optional

import strawberry
from graphql import GraphQLError
from rest_framework import serializers
from strawberry.types import Info

from core.schema.common import GlobalIDUtils, MutationResult, ValidationError, unpack_nested_errors
from core_ui.serializers.component import ComponentSerializer


@strawberry.input
class ComponentChildInput:
    child_component: strawberry.ID
    sort_order: int


@strawberry.input
class ComponentInput:
    id: Optional[strawberry.ID] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    properties: Optional[strawberry.scalars.JSON] = None
    children: Optional[list[ComponentChildInput]] = None
    groups: Optional[list[strawberry.ID]] = None


@strawberry.type
class ComponentMutationResult(MutationResult):
    id: Optional[strawberry.ID] = None


@strawberry.type
class Mutation:

    @strawberry.mutation
    def component(self, info: Info, input: ComponentInput) -> ComponentMutationResult:
        """Create or update a Component."""
        from core_ui.models import Component

        user = info.context.user
        model = Component

        # Permission check
        instance = None
        if input.id:
            pk = GlobalIDUtils.get_pk_flexible(input.id)
            instance = Component.objects.filter(pk=pk).first()
            if not instance:
                raise GraphQLError(f'Component {input.id} not found')
            model.p('model').change.check(user)
        else:
            model.p('model').add.check(user)

        # Build serializer data
        data = {}
        for field_name in ['name', 'slug', 'description', 'is_active', 'path', 'icon', 'properties']:
            value = getattr(input, field_name, None)
            if value is not None:
                data[field_name] = value

        # Handle children with sort_order validation
        if input.children is not None:
            children = []
            order_dict = {}
            for child in input.children:
                if child.sort_order in order_dict:
                    raise GraphQLError("sortOrder must be unique")
                order_dict[child.sort_order] = child.child_component

            for i in range(len(order_dict)):
                if i not in order_dict:
                    raise GraphQLError("sort_order must be a positive numeric sequence from zero.")
                child_pk = GlobalIDUtils.get_pk_flexible(order_dict[i])
                child_obj = Component.objects.filter(pk=child_pk).first()
                if not child_obj:
                    raise GraphQLError(f'Child component {order_dict[i]} not found')
                children.append({'sort_order': i, 'child_component': child_obj.pk})
            data['children'] = children

        # Handle groups
        if input.groups is not None:
            from django.contrib.auth.models import Group
            group_pks = []
            for group_id in input.groups:
                pk = GlobalIDUtils.get_pk_flexible(group_id)
                group = Group.objects.filter(pk=pk).first()
                if not group:
                    raise GraphQLError(f'Group {group_id} not found')
                group_pks.append(group.pk)
            data['groups'] = group_pks

        data['updated_by_id'] = user.id
        if instance is None:
            data['created_by_id'] = user.id

        # Run serializer
        kwargs = {
            'data': data,
            'partial': True,
            'context': {'request': info.context},
        }
        if instance is not None:
            kwargs['instance'] = instance

        serializer = ComponentSerializer(**kwargs)
        if serializer.is_valid():
            obj = serializer.save()
            global_id = GlobalIDUtils.to_global_id('ComponentType', obj.pk)
            return ComponentMutationResult(ok=True, errors=[], id=global_id)

        errors = unpack_nested_errors(serializer.errors)
        return ComponentMutationResult(ok=False, errors=errors)
