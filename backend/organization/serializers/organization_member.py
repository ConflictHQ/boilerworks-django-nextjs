from django.contrib.auth.models import User
from organization.models import OrganizationMember
from organization.signals import organization_member_activation_changed
from rest_framework import serializers


class OrganizationMemberSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=True,
                                         help_text='Whether the employee is currently active øn the organization.')

    user_id = serializers.CharField(max_length=32, required=True, allow_null=True,
                                    help_text="The user id of the employee to be activated/deactivated")

    organization_id = serializers.CharField(max_length=32, required=False,
                                            help_text="The organization id that employee will be affiliated to."
                                                      "defaults to the requesters' organization")

    class Meta:
        model = OrganizationMember
        fields = ['is_active', 'user_id', 'organization_id']

    def update(self, instance, validated_data):
        """
        Update organization member activation status.

        Sends organization_member_activation_changed signal to allow domain apps
        to respond to activation changes without hard dependencies.
        """
        is_active = validated_data["is_active"]
        user_id = validated_data['user_id']

        # Update user and member activation status
        User.objects.filter(id=user_id).update(is_active=is_active)
        instance.member.is_active = is_active
        instance.is_active = is_active
        instance.save()

        # Send signal for domain apps to handle their own updates
        organization_member_activation_changed.send(
            sender=self.__class__,
            instance=instance,
            is_active=is_active,
            user_id=user_id,
        )

        return instance
