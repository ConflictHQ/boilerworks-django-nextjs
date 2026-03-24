from typing import Dict, List, Tuple

from config.roles_gen import P
from core.models import Address, Profile
from core.serializers import FieldRestrictedSerializer
from core.serializers.address import AddressSerializer
from core.serializers.user import UserSerializer
from django.contrib.auth.models import User
from pushnotif.service import BroadcastNotification
from rest_framework import serializers

# Optional import - Domain-specific functionality
try:
    from domain_app.models import ApprovalRequest
    HAS_DOMAIN_APP = True
except ImportError:
    ApprovalRequest = None
    HAS_DOMAIN_APP = False


class ProfileSerializer(FieldRestrictedSerializer):
    address = AddressSerializer(required=False)
    birth_date = serializers.DateField(required=False, allow_null=True, help_text="Date of birth of the employee. Format: YYYY-MM-DD")
    user = UserSerializer(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = Profile
        exclude = [
            'created_at',
            'created_by',
            'updated_at',
            'updated_by',
            'version',
            'signature',
            'avatar',
        ]

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        user_id = validated_data.pop('user_id', None)
        address = Address.objects.create(**address_data)
        instance = Profile.objects.create(**validated_data)
        if user_id is not None:
            instance.user_id = user_id
        instance.address = address
        return instance

    def update(self, instance, validated_data):
        original, draft = Profile.objects.get_draft(instance)
        if 'address' in validated_data:
            addr_whitelist, addr_data = ProfileSerializer.extract_whitelisted(
                instance.address, validated_data.pop('address')
            )
            if addr_whitelist:
                Address.objects.filter(id=instance.address_id).update(**addr_whitelist)
                if draft:
                    Address.objects.filter(id=draft.address_id).update(**addr_whitelist)
            if addr_data:
                validated_data['address'] = addr_data
        whitelisted, validated_data = ProfileSerializer.extract_whitelisted(instance, validated_data)
        self.update_whitelisted(original, draft, whitelisted)
        if not validated_data:
            return instance

        # Use approval request if domain app is available
        if HAS_DOMAIN_APP:
            with ApprovalRequest.objects.for_instance(
                    instance=draft,
                    permission=P.PROFILE_APPROVE_CHANGES.perm(),
                    created_by=original.user,
            ) as context:
                instance: Profile = draft
                instance.document_option = Profile.DocumentOptions.DRAFTED
                user_data = validated_data.pop('user', {})
                if 'first_name' in validated_data:
                    user_data = {
                                    'first_name': validated_data.get('first_name')
                                } | user_data
                if 'last_name' in validated_data:
                    user_data = {
                                    'last_name': validated_data.get('last_name')
                                } | user_data
                if user_data:
                    User.objects.filter(id=user_data.pop('id', original.user.id)).update(**user_data)
                if 'address' in validated_data:
                    address_data = validated_data.pop('address')
                    if instance.address_id is None:
                        address = Address.objects.create(**address_data)
                        setattr(instance, "address_id", address.id)
                    else:
                        Address.objects.filter(id=instance.address_id).update(**address_data)

                for key, value in validated_data.items():
                    setattr(instance, key, value)
                instance.save()
            self.send_approval_notification(instance, context.request)
        else:
            # Without domain app, directly update profile
            instance: Profile = draft
            user_data = validated_data.pop('user', {})
            if user_data:
                User.objects.filter(id=user_data.pop('id', original.user.id)).update(**user_data)
            if 'address' in validated_data:
                address_data = validated_data.pop('address')
                if instance.address_id is None:
                    address = Address.objects.create(**address_data)
                    setattr(instance, "address_id", address.id)
                else:
                    Address.objects.filter(id=instance.address_id).update(**address_data)

            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.save()

        return instance

    def send_approval_notification(self, instance: Profile, approval_request):
        """Send approval notification (Domain-specific)."""
        if not HAS_DOMAIN_APP:
            return

        try:
            from domain_app.notifications import Notifications, ProfileApprovalBroadcastParameters

            request = self.context.get('request', None)
            requester = request.user if request else None
            target_user = instance.parent.user if instance.parent else instance.user

            notif_params = ProfileApprovalBroadcastParameters(
                original_sender=requester,
                broadcast_recipient=None,
                updated_user=target_user
            )
            approval_notification = BroadcastNotification(
                notification=None,
                broadcast_notification=Notifications.PROFILE_APPROVAL_BROADCAST
            )
            approval_notification(
                notification_parameters=notif_params,
                sender=requester if request.user != target_user else target_user,
                recipient=None,
                instance=approval_request,
                on_behalf_of=target_user
            )
        except ImportError:
            # domain app not available - skip notification
            pass

    @staticmethod
    def update_whitelisted(original: Profile, draft: Profile, whitelisted: dict):
        if not whitelisted:
            return
        for key, value in whitelisted.items():
            setattr(original, key, value)
            original.save()
            if draft:
                setattr(draft, key, value)
                draft.save()

    @classmethod
    def extract_whitelisted(cls, instance, validated_data: dict) -> Tuple[dict, dict]:
        # Fixme extract to util/refactor so that it can be share seamlessly accross types
        whitelist: List[str] = instance.whitelist_fields() if hasattr(instance, 'whitelist_fields') else []
        result = {}
        for field in whitelist:
            if field not in validated_data:
                continue

            if validated_data.get(field) != getattr(instance, field, None):
                result[field] = validated_data.pop(field)
        if cls.recursive_equality_check(instance, validated_data):
            validated_data = {}
        return result, validated_data

    @classmethod
    def recursive_equality_check(cls, instance, data: Dict):
        response = True
        for key, value in data.items():
            if isinstance(data[key], dict) and hasattr(instance, key):
                response = response and cls.recursive_equality_check(getattr(instance, key), data[key])
                continue
            if hasattr(instance, key) and getattr(instance, key) != value:
                return False
        return response
