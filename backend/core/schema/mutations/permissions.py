from config.permissions import AbstractPermissions
from core.schema.mutations.restricted_serializer_mutation import RestrictedSerializerMutation
from core.serializers.permissions import UserGroupSerializer
from core.systems import Action


class GroupOperationMutation(RestrictedSerializerMutation):
    class Meta:
        serializer_class = UserGroupSerializer
        fields = "__all__"

    @classmethod
    def has_model_permissions(cls, model, user, instance_id=None):
        AbstractPermissions.check_django_auth_permission(user, 'user', Action.CHANGE, True)
        AbstractPermissions.check_django_auth_permission(user, 'group', Action.CHANGE, True)

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        from core.schema import GroupType, UserType
        user_pks = []
        for user_id in input.pop('user_ids'):
            user_pks.append(UserType.get_object(global_id=user_id, info=info, raise_not_found=True).id)
        input['user_ids'] = user_pks
        input['group_id'] = GroupType.get_object(global_id=input.pop('group_id'), info=info, raise_not_found=True).id

        input['operation'] = input['operation'].value
        return {'data': input, 'partial': True}

    @classmethod
    def response(cls, ok, errors):
        return GroupOperationMutation(ok=ok, errors=errors)
