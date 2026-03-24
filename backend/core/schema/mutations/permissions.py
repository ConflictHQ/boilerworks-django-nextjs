"""Permission mutations migrated from Graphene to Strawberry."""
from __future__ import annotations

import strawberry
from strawberry.types import Info

from config.permissions import AbstractPermissions
from core.serializers.permissions import UserGroupSerializer
from core.schema.common import GlobalIDUtils, MutationResult
from core.systems import Action


@strawberry.input
class GroupOperationInput:
    user_ids: list[strawberry.ID]
    group_id: strawberry.ID
    operation: str


@strawberry.type
class PermissionMutations:

    @strawberry.mutation(description="Add or remove users from a permission group.")
    def permission_group_operation(self, info: Info, input: GroupOperationInput) -> MutationResult:
        user = info.context.user

        # Permission checks (mirrors RestrictedSerializerMutation.has_model_permissions)
        AbstractPermissions.check_django_auth_permission(user, 'user', Action.CHANGE, True)
        AbstractPermissions.check_django_auth_permission(user, 'group', Action.CHANGE, True)

        # Resolve global IDs to PKs
        from core.schema import GroupType, UserType
        user_pks = []
        for user_id in input.user_ids:
            user_pks.append(UserType.get_object(global_id=user_id, info=info, raise_not_found=True).id)

        group_id = GroupType.get_object(global_id=input.group_id, info=info, raise_not_found=True).id

        data = {
            'user_ids': user_pks,
            'group_id': group_id,
            'operation': input.operation,
        }

        serializer = UserGroupSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return MutationResult.success()
        else:
            return MutationResult.from_serializer_errors(serializer.errors)
