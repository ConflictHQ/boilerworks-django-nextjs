from django.contrib.auth import get_user_model
from django.test import TestCase

from workflows.models import WorkflowDefinition

User = get_user_model()


class WorkflowDefinitionTypeTest(TestCase):

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='TestOrg')
        self.user = User.objects.create_superuser(
            username='workflowDefinition_test', email='workflowDefinition@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.instance = WorkflowDefinition.objects.create(
            name='Test WorkflowDefinition',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_instance_created(self):
        obj = WorkflowDefinition.objects.get(pk=self.instance.pk)
        self.assertEqual(obj.name, 'Test WorkflowDefinition')
        self.assertIsNotNone(obj.guid)
        self.assertIsNotNone(obj.slug)

    def test_instance_has_tracking_fields(self):
        obj = WorkflowDefinition.objects.get(pk=self.instance.pk)
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        self.assertEqual(obj.created_by, self.user)
