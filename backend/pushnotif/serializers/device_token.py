from enum import Enum

from core.serializers.restricted_model_serializer import FieldRestrictedSerializer
from pushnotif.models import DeliveryMethods, DeviceToken
from rest_framework import serializers


class DeviceTokenOperation(Enum):
    SUBSCRIBE = 'Subscribe'
    UNSUBSCRIBE = 'Unsubscribe'


class DeviceTokenSerializer(FieldRestrictedSerializer):
    recipient_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    device_token = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    name = serializers.CharField(max_length=128, allow_blank=True, allow_null=True)
    created_by_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    updated_by_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    delivery_method_id = serializers.ChoiceField(choices=[method.name for method in DeliveryMethods], required=False)
    device_operation = serializers.ChoiceField(
        required=False,
        write_only=True,
        choices=[
            (operation.name, operation.value) for operation in
            DeviceTokenOperation
        ]
    )

    class Meta:
        model = DeviceToken
        fields = [
            'created_by_id',
            'delivery_method_id',
            'device_token',
            'device_operation',
            'name',
            'recipient_id',
            'updated_by_id'
        ]

    def create(self, validated_data):
        instance = DeviceToken.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        # Update  supports the behavior for people who may share a mobile device
        # as firebase will reassign the same token, regardless of user, unless it has expired in their end.
        # Do not update any other attribute
        setattr(instance, 'recipient_id', validated_data.pop('recipient_id'))
        setattr(instance, 'updated_by_id', validated_data.pop('updated_by_id'))
        instance.save()
        return instance
