from core.models import Notification
from core.serializers.restricted_model_serializer import FieldRestrictedSerializer


class NotificationSerializer(FieldRestrictedSerializer):

    class Meta:
        model = Notification
        fields = ['user', 'subject', 'message']
        read_only_fields = ['status_date', 'created_by', 'created_at']

    def to_internal_value(self, data):
        from core.schema import UserType
        data['user'] = UserType.get_pk(data.get('user'))
        return super().to_internal_value(data)

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().update(instance, validated_data)
