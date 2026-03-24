from core.serializers import BaseModelSerializer
from pushnotif.models import NotificationConfig


class NotificationConfigSerializer(BaseModelSerializer):
    class Meta:
        model = NotificationConfig
        fields = ["delivery_method_template", "is_enabled"]

    def create(self, validated_data, **kwargs):
        user = self.context["request"].user
        return NotificationConfig.objects.create(
            profile=user.profile,
            delivery_method_template=validated_data["delivery_method_template"],
            is_enabled=validated_data["is_enabled"],
            created_by=user,
        )

    def update(self, instance, validated_data):
        instance.is_enabled = validated_data.get("is_enabled", instance.is_enabled)
        instance.updated_by = self.context["request"].user
        instance.save()
        return instance
