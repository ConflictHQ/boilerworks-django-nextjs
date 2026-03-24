from typing import Dict

from config.permissions import AbstractPermissions
from core.models import Profile
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class FieldRestrictedSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ['created_at', 'created_by', 'updated_at', 'updated_by', 'version']

    def to_internal_value(self, data):
        # This method performs validation when doing write operations with serializers
        if 'request' in self.context:
            blocked_fields = self.check_permissions(self, data)
            if blocked_fields:
                AbstractPermissions.denied(self.context['request'].user, blocked_fields)

        return super().to_internal_value(data)

    @classmethod
    def check_permissions(cls, root: ModelSerializer, data: Dict, prefix: str = None):
        response = []

        for key, value in data.items():
            serializer_field = root.fields[key]
            if isinstance(serializer_field, serializers.ModelSerializer):
                # Nested serializer, evaluate permissions recursively
                response.extend(
                    cls.check_permissions(serializer_field, value, prefix=f'{prefix}.{key}' if prefix else key))

            # Permission rules for the User model are specified in Profile
            permission = Profile.p(key).change if root.Meta.model is get_user_model() else root.Meta.model.p(key).change
            # Ignore fields that do not belong to the model and do not represent a nested serializer
            if not permission:
                # No permission record is found, currently writing is allowed by default for this scenario
                continue
            user = root.context['request'].user
            if not permission.by(user):
                permission.log_denied(user, False, f'User has no permission to modify field {key}.')
                # User has no permission to modify field, add it to error response
                response.append(f'{prefix}.{key}' if prefix else key)
                continue

        return response
