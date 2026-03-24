from enum import Enum

from django.contrib.auth.models import Group
from rest_framework import serializers


class UserGroupOperation(Enum):
    ADD = 'Add'
    REMOVE = 'Remove'


class UserGroupSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.CharField(
            required=True,
            help_text='Id of the user to be added/remove from group.'),
        required=True,
        help_text='List with ids of users to be added/removed from group.')
    group_id = serializers.CharField(required=True, help_text='Id of the group to be modified.')
    operation = serializers.ChoiceField(required=True,
                                        choices=[(operation.name, operation.value) for operation in UserGroupOperation])

    def save(self, **kwargs):
        group = Group.objects.get(pk=self.validated_data['group_id'])
        if self.validated_data['operation'] == UserGroupOperation.REMOVE.name:
            group.user_set.remove(*self.validated_data['user_ids'])
        else:
            group.user_set.add(*self.validated_data['user_ids'])
        group.save()
        return self.validated_data
