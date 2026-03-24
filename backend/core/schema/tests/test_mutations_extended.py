"""Extended mutation tests — model-level and integration tests for remaining coverage."""
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from django.utils import timezone

from config.schema import schema
from core.schema.context import StrawberryContext

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class PinModelTest(TestCase):
    """Tests for PIN update on Profile model."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='PinOrg')
        self.user = User.objects.create_superuser(
            username='pin_user', email='pin@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def test_update_pin_sets_hash(self):
        self.user.profile.update_pin('1234')
        self.user.profile.refresh_from_db()
        self.assertIsNotNone(self.user.profile.pin)
        self.assertGreater(len(self.user.profile.pin), 4)

    def test_has_pin_false_initially(self):
        self.assertFalse(self.user.profile.pin)

    def test_has_pin_true_after_set(self):
        self.user.profile.update_pin('5678')
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.pin)


class NotificationModelTest(TestCase):
    """Tests for Notification model."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='NotifOrg')
        self.user = User.objects.create_superuser(
            username='notif_user', email='notif@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def test_create_notification(self):
        from core.models import Notification
        n = Notification.objects.create(
            user=self.user, subject='Test', message='Hello',
            created_by=self.user, updated_by=self.user,
        )
        self.assertEqual(n.subject, 'Test')
        self.assertEqual(n.user, self.user)

    def test_default_status_is_unread(self):
        from core.models import Notification, NotificationStatus
        n = Notification.objects.create(
            user=self.user, subject='Unread', message='Check',
            created_by=self.user, updated_by=self.user,
        )
        self.assertEqual(n.status, NotificationStatus.UNREAD)

    def test_mark_as_read(self):
        from core.models import Notification, NotificationStatus
        n = Notification.objects.create(
            user=self.user, subject='Read Me', message='Now',
            created_by=self.user, updated_by=self.user,
        )
        n.status = NotificationStatus.READ
        n.status_date = timezone.now()
        n.save()
        n.refresh_from_db()
        self.assertEqual(n.status, NotificationStatus.READ)


class UploadModelTest(TestCase):
    """Tests for Upload model."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='UpOrg')
        self.user = User.objects.create_superuser(
            username='up_user', email='up@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def test_upload_create(self):
        from core.models import Upload
        u = Upload.objects.create(
            name='photo.jpg', content_type='image/jpeg',
            created_by=self.user, updated_by=self.user,
        )
        self.assertEqual(u.name, 'photo.jpg')
        self.assertIsNotNone(u.id)

    def test_upload_soft_delete(self):
        from core.models import Upload
        u = Upload.objects.create(
            name='del.png', content_type='image/png',
            created_by=self.user, updated_by=self.user,
        )
        u.deleted_at = timezone.now()
        u.deleted_by = self.user
        u.save()
        self.assertTrue(Upload.objects.filter(pk=u.pk).exists())
        self.assertIsNotNone(u.deleted_at)

    def test_upload_global_id_property(self):
        from core.models import Upload
        from strawberry.relay import from_base64
        u = Upload.objects.create(
            name='gid.pdf', content_type='application/pdf',
            created_by=self.user, updated_by=self.user,
        )
        gid = u.global_id
        type_name, pk = from_base64(gid)
        self.assertEqual(type_name, 'UploadType')
        self.assertEqual(str(pk), str(u.pk))


class OrganizationMemberModelTest(TestCase):
    """Tests for OrganizationMember model."""

    def test_create_and_deactivate(self):
        from organization.models import Organization, OrganizationMember
        org = Organization.objects.create(name='OmOrg')
        user = User.objects.create_user(username='om_u', email='om@t.com', password='x')
        m = OrganizationMember.objects.create(organization=org, member=user, is_active=True)
        self.assertTrue(m.is_active)
        m.is_active = False
        m.save()
        m.refresh_from_db()
        self.assertFalse(m.is_active)

    def test_organization_has_guid(self):
        from organization.models import Organization
        org = Organization.objects.create(name='GidOrg')
        self.assertIsNotNone(org.guid)
        self.assertIsNotNone(org.slug)
