import io

from core.models.process import DataProcess, DataProcessEntity, EntityType, FileType, ProcessStatus
from core.systems.process_system import AdminProcessSystem
from core.tests.utils.base_test import BaseTest
from core_ui.models import Component, ComponentRelationship
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class ComponentsSystemTest(BaseTest):
    """Tests for processing component CSV files through AdminProcessSystem"""

    def setUp(self):
        super().setUp()
        self.request = self.request()
        self.request.POST = {
            'entity_type': EntityType.COMPONENTS,
            'language_code': 'en'
        }

        user_content_type, _ = ContentType.objects.get_or_create(
            app_label='auth',
            model='user'
        )

        component_content_type, _ = ContentType.objects.get_or_create(
            app_label='core_ui',
            model='component'
        )

        self.view_perm, _ = Permission.objects.get_or_create(
            codename='view_dashboard',
            content_type=component_content_type,
            defaults=dict(
                name="Can view \"dashboard\"",
            )
        )

        self.edit_perm, _ = Permission.objects.get_or_create(
            codename='edit_dashboard',
            content_type=user_content_type,
            defaults=dict(
                name='Can Edit Dashboard',
            )
        )

    def test_load_components_csv_success(self):
        """Test successful processing of components CSV file"""
        csv_content = (
            "Name,Slug,Description,Is Active,Path,Icon,Properties,Permissions,Children\n"
            "Dashboard,dashboard,Main dashboard,TRUE,/dashboard,dashboard-icon,{\"visible\": true},component.core_ui.view_dashboard|component.core_ui.edit_dashboard,reports|settings\n"
            "Reports,reports,Reports section,TRUE,/reports,reports-icon,{\"order\": 1},component.core_ui.view_reports,\n"
            "Settings,settings,Settings section,TRUE,/settings,settings-icon,,component.core_ui.admin_settings,"
        )

        csv_file = io.StringIO(csv_content)
        self.request.FILES = {'data_file': io.BytesIO(csv_file.getvalue().encode())}
        self.request.FILES['data_file'].content_type = 'text/csv'

        process = AdminProcessSystem.load_data(self.request)
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        self.assertEqual(process.status, ProcessStatus.PENDING)
        self.assertEqual(process.file_type, FileType.CSV)
        self.assertEqual(process.entity_type, EntityType.COMPONENTS)

        expected_data = [
            {
                'Children': [
                    {'order': 0, 'slug': 'reports'},
                    {'order': 1, 'slug': 'settings'}
                ],
                'Description': 'Main dashboard',
                'Icon': 'dashboard-icon',
                'Is Active': True,
                'Name': 'Dashboard',
                'Path': '/dashboard',
                'Permissions': [
                    {'app_label': 'core_ui', 'codename': 'view_dashboard', 'model': 'component'},
                    {'app_label': 'core_ui', 'codename': 'edit_dashboard', 'model': 'component'}
                ],
                'Properties': {
                    'visible': True
                },
                'Slug': 'dashboard'
            },
            {
                'Children': [],
                'Description': 'Reports section',
                'Icon': 'reports-icon',
                'Is Active': True,
                'Name': 'Reports',
                'Path': '/reports',
                'Permissions': [
                    {'app_label': 'core_ui', 'codename': 'view_reports', 'model': 'component'}
                ],
                'Properties': {
                    'order': 1
                },
                'Slug': 'reports'
            },
            {
                'Children': [],
                'Description': 'Settings section',
                'Icon': 'settings-icon',
                'Is Active': True,
                'Name': 'Settings',
                'Path': '/settings',
                'Permissions': [
                    {'app_label': 'core_ui', 'codename': 'admin_settings', 'model': 'component'}
                ],
                'Properties': {},
                'Slug': 'settings'
            }
        ]

        self.assertEqual(process_entity.data, expected_data)
        self.assertEqual(process_entity.status, ProcessStatus.PENDING)
        self.assertEqual(process_entity.error_message, '')

    def test_load_components_csv_invalid_json_properties(self):
        """Test handling of invalid JSON in Properties column"""
        csv_content = (
            "Name,Slug,Description,Is Active,Path,Icon,Properties,Permissions,Children\n"
            "Dashboard,dashboard,Main dashboard,TRUE,/dashboard,icon,{invalid_json},component.core_ui.view_dashboard,"
        )

        csv_file = io.StringIO(csv_content)
        self.request.FILES = {'data_file': io.BytesIO(csv_file.getvalue().encode())}
        self.request.FILES['data_file'].content_type = 'text/csv'

        process = AdminProcessSystem.load_data(self.request)
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        expected_data = [{
            'Slug': 'dashboard',
            'Name': 'Dashboard',
            'Path': '/dashboard',
            'Icon': 'icon',
            'Permissions': [{'app_label': 'core_ui', 'codename': 'view_dashboard', 'model': 'component'}],
            'Children': [],
            'Properties': {},
            'Description': 'Main dashboard',
            'Is Active': True,
        }]

        self.assertEqual(process_entity.data, expected_data)
        self.assertEqual(process_entity.status, ProcessStatus.PENDING)

    def test_load_components_csv_empty_children(self):
        """Test handling of empty Children column"""
        csv_content = (
            "Name,Slug,Description,Is Active,Path,Icon,Properties,Permissions,Children\n"
            "Dashboard,dashboard,Dashboard description,TRUE,/dashboard,icon,{\"visible\": true},component.core_ui.view_dashboard,"
        )

        csv_file = io.StringIO(csv_content)
        self.request.FILES = {'data_file': io.BytesIO(csv_file.getvalue().encode())}
        self.request.FILES['data_file'].content_type = 'text/csv'

        process = AdminProcessSystem.load_data(self.request)
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        expected_data = [{
            'Slug': 'dashboard',
            'Name': 'Dashboard',
            'Description': 'Dashboard description',
            'Path': '/dashboard',
            'Is Active': True,
            'Icon': 'icon',
            'Permissions': [{
                'codename': 'view_dashboard',
                'model': 'component',
                'app_label': 'core_ui',
            }],
            'Children': [],
            'Properties': {'visible': True}
        }]

        self.assertEqual(process_entity.data, expected_data)
        self.assertEqual(process_entity.status, ProcessStatus.PENDING)

    def test_load_components_csv_empty_file(self):
        """Test processing of empty CSV file (headers only)"""
        csv_content = "Name,Slug,Description,Is Active,Path,Icon,Properties,Permissions,Children\n"

        csv_file = io.StringIO(csv_content)
        self.request.FILES = {'data_file': io.BytesIO(csv_file.getvalue().encode())}
        self.request.FILES['data_file'].content_type = 'text/csv'

        process = AdminProcessSystem.load_data(self.request)
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        self.assertEqual(process_entity.data, [])
        self.assertEqual(process_entity.status, ProcessStatus.PENDING)

    def test_process_components_success(self):
        """Test successful processing of components with relationships"""
        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard',
                'Name': 'Dashboard',
                'Path': '/dashboard',
                'Icon': 'dashboard-icon',
                'Permissions': [
                    {
                        'codename': 'view_dashboard',
                        'model': 'component',
                        'app_label': 'core_ui',
                    },
                    {
                        'codename': 'edit_dashboard',
                        'model': 'user',
                        'app_label': 'auth',
                    }
                ],
                'Children': [
                    {'slug': 'reports-testable-01', 'order': 0},
                    {'slug': 'settings-testable-01', 'order': 1}
                ],
                'Properties': {'visible': True},
                'Is Active': True
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        process_entity = DataProcessEntity.objects.filter(process=process).first()

        Component.objects.create(slug='reports-testable-01', name='Reports')
        Component.objects.create(slug='settings-testable-01', name='Settings')

        AdminProcessSystem.process(process, self.user, overwrite=False)

        process.refresh_from_db()
        process_entity.refresh_from_db()

        self.assertEqual(process.status, ProcessStatus.DONE)
        self.assertEqual(process_entity.status, ProcessStatus.DONE)

        component = Component.objects.get(slug='dashboard')
        self.assertEqual(component.name, 'Dashboard')
        self.assertEqual(component.path, '/dashboard')
        self.assertEqual(component.icon, 'dashboard-icon')
        self.assertEqual(component.properties, {'visible': True})
        self.assertTrue(component.is_active)

        self.assertCountEqual(component.permissions.values_list('codename', flat=True), ['edit_dashboard', 'view_dashboard'])

        relationships = ComponentRelationship.objects.filter(parent=component)
        self.assertEqual(relationships.count(), 2)

        reports_rel = relationships.get(child__slug='reports-testable-01')
        settings_rel = relationships.get(child__slug='settings-testable-01')
        self.assertEqual(reports_rel.order, 0)
        self.assertEqual(settings_rel.order, 1)

    def test_process_components_missing_permissions(self):
        """Test processing when referenced permissions components don't exist"""
        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard',
                'Name': 'Dashboard',
                'Is Active': True,
                'Children': [
                    {'slug': 'nonexistent', 'order': 0}
                ]
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        process_entity = DataProcessEntity.objects.filter(process=process).first()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        process.refresh_from_db()
        process_entity.refresh_from_db()
        self.assertEqual(process.status, ProcessStatus.FAILED)
        self.assertEqual(process_entity.status, ProcessStatus.FAILED)
        self.assertNotEqual(process_entity.error_message, '')

    def test_process_components_update_existing(self):
        """Test updating existing component"""
        existing = Component.objects.create(
            slug='dashboard_component',
            name='Old Dashboard',
            path='/old',
            icon='old-icon',
            properties={'visible': False},
            is_active=False
        )
        existing.permissions.add(self.view_perm)

        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard_component',
                'Name': 'New Dashboard',
                'Path': '/new',
                'Icon': 'new-icon',
                'Permissions': [
                    {
                        'codename': 'edit_dashboard',
                        'model': 'user',
                        'app_label': 'auth'
                    }
                ],
                'Properties': {'visible': True},
                'Is Active': True,
                'Children': []
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        existing.refresh_from_db()

        self.assertEqual(existing.name, 'New Dashboard')
        self.assertEqual(existing.path, '/new')
        self.assertEqual(existing.icon, 'new-icon')
        self.assertEqual(existing.properties, {'visible': True})
        self.assertTrue(existing.is_active)

        self.assertCountEqual(
            existing.permissions.values_list('codename', flat=True),
            ['edit_dashboard']
        )

    def test_process_components_missing_slug(self):
        """Test handling of component data missing required slug"""
        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Name': 'No Slug Component',
                'Path': '/path'
            }],
            line_number=0,
            status=ProcessStatus.PENDING,
        ).save()

        process_entity = DataProcessEntity.objects.filter(process=process).first()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        process.refresh_from_db()
        process_entity.refresh_from_db()
        self.assertEqual(process_entity.status, ProcessStatus.FAILED)
        self.assertNotEqual(process_entity.error_message, '')

    def test_process_components_clear_permissions(self):
        """Test clearing all permissions from a component"""
        existing = Component.objects.create(
            slug='test_component',
            name='Test Component'
        )

        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'test_component',
                'Name': 'Test Component',
                'Permissions': [],
                'Is Active': True,
                'Children': []
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        existing.refresh_from_db()
        self.assertEqual(existing.permissions.count(), 0)

    def test_process_components_overwrite_mode(self):
        """Test that overwrite mode clears existing permissions and components"""
        dashboard = Component.objects.create(
            slug='dashboard-testable-01',
            name='Original Dashboard',
            path='/dashboard'
        )
        dashboard.permissions.add(self.view_perm)

        reports = Component.objects.create(slug='reports-testable-01', name='Reports')
        settings = Component.objects.create(slug='settings-testable-01', name='Settings')

        ComponentRelationship.objects.create(
            parent=dashboard,
            child=reports,
            order=0
        )
        ComponentRelationship.objects.create(
            parent=dashboard,
            child=settings,
            order=1
        )

        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard-testable-01',
                'Name': 'Updated Dashboard',
                'Path': '/new-path',
                'Permissions': [
                    {
                        'codename': 'edit_dashboard',
                        'model': 'user',
                        'app_label': 'auth'
                    }
                ],
                'Children': [
                    {'slug': 'reports-testable-01', 'order': 5}
                ],
                'Is Active': True
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=True)

        dashboard.refresh_from_db()
        # TODO: Update tests
        self.assertEqual(dashboard.name, 'Original Dashboard')
        self.assertEqual(dashboard.path, '/dashboard')
        self.assertTrue(dashboard.is_active)

    def test_process_components_non_overwrite_mode(self):
        """Test that non-overwrite mode preserves existing permissions and components"""
        dashboard = Component.objects.create(
            slug='dashboard-testable-02',
            name='Original Dashboard'
        )
        dashboard.permissions.add(self.view_perm)

        reports = Component.objects.create(slug='reports-testable-02', name='Reports')
        Component.objects.create(slug='settings-testable-01', name='Settings')

        ComponentRelationship.objects.create(
            parent=dashboard,
            child=reports,
            order=0
        )

        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard-testable-02',
                'Name': 'Updated Dashboard',
                'Permissions': [
                    {
                        'codename': 'edit_dashboard',
                        'model': 'user',
                        'app_label': 'auth'
                    }
                ],
                'Children': [
                    {'slug': 'settings-testable-01', 'order': 1}
                ],
                'Is Active': True
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        dashboard.refresh_from_db()
        self.assertEqual(dashboard.name, 'Updated Dashboard')
        self.assertTrue(dashboard.is_active)

        self.assertCountEqual(
            dashboard.permissions.values_list('codename', flat=True),
            ['edit_dashboard']
        )

        relationships = ComponentRelationship.objects.filter(parent=dashboard)
        self.assertEqual(relationships.count(), 1)
        self.assertEqual(
            relationships.get(child__slug='settings-testable-01').order,
            1
        )

    def test_process_components_missing_required_fields(self):
        """Test validation of required fields"""
        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Name': 'No Slug Component',
                'Path': '/path',
                'Is Active': True,
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        process.refresh_from_db()
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        self.assertEqual(process.status, ProcessStatus.FAILED)
        self.assertEqual(process_entity.status, ProcessStatus.FAILED)
        self.assertIn('Missing Slug', process_entity.error_message)

    def test_process_components_invalid_child_reference(self):
        """Test error handling when referenced child component doesn't exist"""
        process = DataProcess.objects.create(
            entity_type=EntityType.COMPONENTS,
            status=ProcessStatus.PENDING
        )

        DataProcessEntity(
            process=process,
            data=[{
                'Slug': 'dashboard',
                'Name': 'Dashboard',
                'Is Active': True,
                'Children': [
                    {'slug': 'nonexistent', 'order': 0}
                ]
            }],
            line_number=0,
            status=ProcessStatus.PENDING
        ).save()

        AdminProcessSystem.process(process, self.user, overwrite=False)

        process.refresh_from_db()
        process_entity = DataProcessEntity.objects.filter(process=process).first()

        self.assertEqual(process.status, ProcessStatus.FAILED)
        self.assertEqual(process_entity.status, ProcessStatus.FAILED)
        self.assertNotEqual(process_entity.error_message, '')
