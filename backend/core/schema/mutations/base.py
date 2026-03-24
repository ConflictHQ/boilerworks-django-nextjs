"""Shared mutation infrastructure for Strawberry GraphQL.

Provides utilities that replace Graphene's SerializerMutation,
RestrictedSerializerMutation, DeleteMutation, and ActivateMutation patterns.
"""
from __future__ import annotations

from typing import Optional

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from core.schema.common import (
    GlobalIDUtils,
    MutationResult,
    unpack_nested_errors,
)


def restricted_serializer_mutate(
    serializer_class,
    model_class,
    info: Info,
    data: dict,
    instance=None,
) -> MutationResult:
    """Execute a DRF serializer mutation with permission checks.

    Replaces RestrictedSerializerMutation.mutate_and_get_payload().

    1. Checks model-level add/change permissions
    2. Runs the serializer
    3. Returns ok/errors MutationResult
    """
    user = info.context.user

    # Permission check
    if instance:
        model_class.p('model').change.check(user)
    else:
        model_class.p('model').add.check(user)

    kwargs = {
        'data': data,
        'partial': True,
        'context': {'request': info.context},
    }
    if instance is not None:
        kwargs['instance'] = instance

    serializer = serializer_class(**kwargs)
    if serializer.is_valid():
        serializer.save()
        return MutationResult.success()

    errors = unpack_nested_errors(serializer.errors)
    return MutationResult(ok=False, errors=errors)


def resolve_instance_from_id(model_class, global_id: str, type_name: str | None = None):
    """Resolve a model instance from a relay global ID or raw PK."""
    pk = GlobalIDUtils.get_pk_flexible(global_id, expected_type=type_name)
    if pk is None:
        raise GraphQLError(f'Invalid ID: {global_id}')
    instance = model_class.objects.filter(pk=pk).first()
    if instance is None:
        raise GraphQLError(f'{model_class.__name__} with ID {global_id} not found')
    return instance


def delete_mutation(info: Info, gid: str) -> bool:
    """Generic soft-delete mutation.

    Finds the object by global ID and calls its delete_check() method.
    Replaces Graphene's DeleteMutation base class.
    """
    type_name, pk = GlobalIDUtils.from_global_id(gid)
    instance = GlobalIDUtils.find_object_by_global_id(gid)
    instance.delete_check(info)
    return True


def activate_mutation(info: Info, gid: str, active: bool = True) -> bool:
    """Generic activate/deactivate mutation.

    Finds the object by global ID and calls its activate() method.
    Replaces Graphene's ActivateMutation base class.
    """
    type_name, pk = GlobalIDUtils.from_global_id(gid)
    instance = GlobalIDUtils.find_object_by_global_id(gid)
    instance.activate(info, active)
    return True
