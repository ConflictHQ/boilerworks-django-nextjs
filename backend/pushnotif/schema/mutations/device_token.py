from core.schema.mutations.restricted_serializer_mutation import RestrictedSerializerMutation
from django.contrib.auth.models import User

from ...models import DeviceToken
from ...serializers.device_token import DeviceTokenOperation, DeviceTokenSerializer


class DeviceTokenMutation(RestrictedSerializerMutation):
    class Meta:
        serializer_class = DeviceTokenSerializer
        fields = "__all__"

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        if 'device_operation' in input and input.pop('device_operation').name == DeviceTokenOperation.UNSUBSCRIBE.name:
            return cls.response(ok=cls.delete(input.get('device_token'), info.context.user), errors=())
        else:
            return super().mutate_and_get_payload(root, info, **input)

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        instance = DeviceToken.objects.filter(device_token=input.get('device_token')).first()
        input['recipient_id'] = info.context.user.id
        if 'delivery_method_id' in input:
            input['delivery_method_id'] = input['delivery_method_id'].value
        if instance is None:
            input['created_by_id'] = info.context.user.id
            input['recipient_id'] = info.context.user.id
            return {'data': input, 'partial': True, "context": {"request": info.context}}
        else:
            input['updated_by_id'] = info.context.user.id
            return {'instance': instance, 'data': input, 'partial': True, "context": {"request": info.context}}

    @classmethod
    def response(cls, ok, errors):
        return DeviceTokenMutation(ok=ok, errors=errors)

    @classmethod
    def delete(cls, device_token: str, user: User) -> bool:
        cls._meta.model_class.p('model').delete.check(user)
        instance = DeviceToken.objects.filter(device_token=device_token).first()
        if instance:
            instance.delete()
        return True
