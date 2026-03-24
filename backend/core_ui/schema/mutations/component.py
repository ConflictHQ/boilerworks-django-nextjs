from core.schema import GroupType, RestrictedSerializerMutation
from core_ui.serializers.component import ComponentSerializer
from rest_framework import serializers


class ComponentMutation(RestrictedSerializerMutation):
    class Meta:
        serializer_class = ComponentSerializer
        fields = '__all__'

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        component_id = input.pop('id', None)
        from core_ui.schema import ComponentType
        instance = None
        if component_id:
            instance = ComponentType.get_object(global_id=component_id, info=info, raise_not_found=True)
        if 'children' in input:
            children = []
            order_dict = {}
            for child in input.pop('children', []):
                if child['sort_order'] in order_dict:
                    raise serializers.ValidationError("sortOrder must be unique")
                order_dict = order_dict | {child['sort_order']: child['child_component']}
            for i in range(0, len(order_dict)):
                if i not in order_dict.keys():
                    raise serializers.ValidationError("sort_order must be a positive numeric sequence from zero.")
                child = {
                    'sort_order': i,
                    'child_component': ComponentType.get_object(
                        global_id=order_dict[i],
                        info=info,
                        raise_not_found=True).pk
                }
                children.append(child)
            input['children'] = children
        if 'groups' in input:
            group_pks = []
            for group in input.pop('groups', []):
                group_pks.append(GroupType.get_object(global_id=group, info=info, raise_not_found=True).pk)
            input['groups'] = group_pks
        input['updated_by_id'] = info.context.user.id
        if instance is None:
            input['created_by_id'] = info.context.user.id
            return {'data': input, 'partial': True, "context": {"request": info.context}}
        else:
            return {'instance': instance, 'data': input, 'partial': True, "context": {"request": info.context}}

    @classmethod
    def response(cls, ok, errors):
        return ComponentMutation(ok=ok, errors=errors)
