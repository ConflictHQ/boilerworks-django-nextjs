from core.schema import RestrictedSerializerMutation
from graphql_relay import from_global_id
from pushnotif.models import NotificationConfig
from pushnotif.serializers.notification_config import NotificationConfigSerializer


class NotificationConfigMutation(RestrictedSerializerMutation):
    class Meta:
        serializer_class = NotificationConfigSerializer
        lookup_field = "id"

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        _, pk = from_global_id(input["delivery_method_template"])

        instance = NotificationConfig.objects.filter(
            profile=info.context.user.profile,
            delivery_method_template=pk
        ).first()

        input['delivery_method_template'] = pk
        if instance:
            return {'instance': instance, 'data': input, 'partial': True, "context": {"request": info.context}}
        else:
            return {'data': input, 'partial': True, "context": {"request": info.context}}


class NotificationConfigMutations:
    notification_config = NotificationConfigMutation.Field()
