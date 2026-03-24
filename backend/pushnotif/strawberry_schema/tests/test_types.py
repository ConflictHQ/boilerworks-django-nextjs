from unittest.mock import MagicMock, PropertyMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from pushnotif.models import (
    DeliveryMethod,
    DeliveryMethodNotificationTemplate,
    DeviceToken,
    NotificationConfig,
    NotificationTemplate,
)
from pushnotif.strawberry_schema.types import (
    DeliveryMethodNotificationTemplateType,
    DeliveryMethodType,
    DeviceTokenType,
    NotificationConfigType,
)

User = get_user_model()


class DeviceTokenTypeTest(TestCase):
    """Tests for DeviceTokenType Strawberry type."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='PushNotifTestOrg')
        self.user = User.objects.create_superuser(
            username='device_test', email='device@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.delivery_method, _ = DeliveryMethod.objects.get_or_create(
            name='ANDROID', defaults={'display_name': 'Android'},
        )
        self.device = DeviceToken.objects.create(
            device_token='test-token-abc',
            name='Test Phone',
            recipient=self.user,
            delivery_method=self.delivery_method,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_device_token_type_has_expected_fields(self):
        """DeviceTokenType should expose delivery_method and name fields."""
        field_names = {f.name for f in DeviceTokenType.__strawberry_definition__.fields}
        self.assertIn('name', field_names)
        self.assertIn('delivery_method', field_names)

    def test_device_token_persisted_with_expected_values(self):
        """DeviceToken model is saved and retrievable with correct field values."""
        token = DeviceToken.objects.get(device_token='test-token-abc')
        self.assertEqual(token.name, 'Test Phone')
        self.assertEqual(token.recipient, self.user)
        self.assertEqual(token.delivery_method, self.delivery_method)


class NotificationConfigFilterTest(TestCase):
    """Tests for NotificationConfigType queryset filtering."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='ConfigTestOrg')
        self.user = User.objects.create_superuser(
            username='config_test', email='config@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.other_user = User.objects.create_user(
            username='other_config', email='other_config@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.other_user, is_active=True,
        )
        self.other_user.profile.active_organization = self.org
        self.other_user.profile.save()

        self.delivery_method, _ = DeliveryMethod.objects.get_or_create(
            name='EMAIL', defaults={'display_name': 'Email'},
        )
        self.template = NotificationTemplate.objects.create(
            name='test_template', display_name='Test Template',
            created_by=self.user, updated_by=self.user,
        )
        self.dm_template = DeliveryMethodNotificationTemplate.objects.create(
            notification_template=self.template,
            delivery_method=self.delivery_method,
            created_by=self.user,
            updated_by=self.user,
        )

        self.config = NotificationConfig.objects.create(
            profile=self.user.profile,
            delivery_method_template=self.dm_template,
            is_enabled=True,
            created_by=self.user,
            updated_by=self.user,
        )
        self.other_config = NotificationConfig.objects.create(
            profile=self.other_user.profile,
            delivery_method_template=self.dm_template,
            is_enabled=False,
            created_by=self.other_user,
            updated_by=self.other_user,
        )

    def _make_info(self, user):
        """Build a mock Info object with context.user set."""
        info = MagicMock()
        info.context.user = user
        info.context.user.is_authenticated = user.is_authenticated
        return info

    def test_authenticated_user_sees_only_own_configs(self):
        """Configs should be filtered to the requesting user's profile."""
        own_configs = NotificationConfig.objects.filter(profile=self.user.profile)
        self.assertIn(self.config, own_configs)
        self.assertNotIn(self.other_config, own_configs)

    def test_unauthenticated_user_sees_no_configs(self):
        """No configs should be returned for anonymous users."""
        qs = NotificationConfig.objects.none()
        self.assertEqual(qs.count(), 0)


class DeliveryMethodNotificationTemplateTypeTest(TestCase):
    """Tests for DeliveryMethodNotificationTemplateType."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='DMTTestOrg')
        self.user = User.objects.create_superuser(
            username='dmt_test', email='dmt@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.delivery_method, _ = DeliveryMethod.objects.get_or_create(
            name='SMS', defaults={'display_name': 'SMS'},
        )
        self.template = NotificationTemplate.objects.create(
            name='sms_template', display_name='SMS Template',
            created_by=self.user, updated_by=self.user,
        )
        self.dm_template = DeliveryMethodNotificationTemplate.objects.create(
            notification_template=self.template,
            delivery_method=self.delivery_method,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_type_has_user_notification_config_field(self):
        """DeliveryMethodNotificationTemplateType should expose user_notification_config."""
        field_names = {
            f.name for f in DeliveryMethodNotificationTemplateType.__strawberry_definition__.fields
        }
        self.assertIn('user_notification_config', field_names)

    def test_user_notification_config_lookup_returns_existing(self):
        """Querying NotificationConfig by profile + template finds the right record."""
        config = NotificationConfig.objects.create(
            profile=self.user.profile,
            delivery_method_template=self.dm_template,
            is_enabled=False,
            created_by=self.user,
            updated_by=self.user,
        )

        result = NotificationConfig.objects.filter(
            profile=self.user.profile,
            delivery_method_template=self.dm_template,
        ).first()
        self.assertEqual(result.pk, config.pk)
        self.assertFalse(result.is_enabled)

    def test_user_notification_config_default_when_missing(self):
        """When no config exists, a default unsaved instance should be creatable."""
        result = NotificationConfig.objects.filter(
            profile=self.user.profile,
            delivery_method_template=self.dm_template,
        ).first()
        self.assertIsNone(result)

        # The resolver creates an unsaved default
        default = NotificationConfig(
            profile=self.user.profile,
            delivery_method_template=self.dm_template,
            is_enabled=True,
        )
        self.assertIsNone(default.pk)
        self.assertTrue(default.is_enabled)
