"""Integration tests for upload mutations (issue #66).

Exercises preSignedUrlImageUpload, confirmPreSignedUrlImageUpload, fileUpload,
processFile and profileImageFieldUpload end-to-end through the assembled schema.

S3/MinIO is never touched: the boto3-backed presign/get helpers on the Upload
model are patched at the classmethod boundary (moto is not a dev dependency),
so everything between the GraphQL layer and the storage call is real.
"""
import sys
import types
from unittest.mock import patch

from config.schema import schema
from core.models import Profile, SharedDirectory, SharedFile
from core.models.process import DataProcess, DataProcessEntity, EntityType, FileType, ProcessStatus
from core.models.upload import FileUpload, Upload
from core.schema.common import GlobalIDUtils
from core.schema.context import StrawberryContext
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from graphql import GraphQLError

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


def _fake_get_object(model):
    """Build a get_object(info, gid, ...) resolving a relay gid against a model."""

    def get_object(info, global_id, raise_not_found=True, **kwargs):
        _, pk = GlobalIDUtils.from_global_id(global_id)
        obj = model.objects.filter(pk=pk).first()
        if obj is None and raise_not_found:
            raise GraphQLError(f'Object id {model.__name__}:{global_id} not found')
        return obj

    return get_object


def _patch_core_schema_types(**type_names):
    """Inject legacy Graphene type lookups the mutations still import.

    The mutations do `from core.schema import UploadType` at call time;
    core.schema.__init__ doesn't export these types, so we inject fakes whose
    get_object resolves against the real database (same pattern as
    test_mutations.py NotificationReadMutationTest._patch_get_object).
    """
    injected = {}
    for name, model in type_names.items():
        fake_type = types.SimpleNamespace()
        fake_type.get_object = staticmethod(_fake_get_object(model))
        injected[name] = fake_type
    return patch.dict(sys.modules['core.schema'].__dict__, injected)


def _patch_presign():
    """Patch the boto3-backed presign helpers on Upload with deterministic URLs."""
    return (
        patch.object(
            Upload, 'generate_pre_signed_url_for_put',
            side_effect=lambda name, parameters=None, expire=None, content_type=None:
                f'https://s3.test/{name}?X-Amz-Signature=put-sig',
        ),
        patch.object(
            Upload, 'generate_pre_signed_url_for_get',
            side_effect=lambda name, parameters=None, expire=None, content_type=None:
                f'https://s3.test/{name}?X-Amz-Signature=get-sig',
        ),
    )


class UploadMutationTestBase(TestCase):
    """Shared setup: org-scoped superuser and patched presign helpers."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='UploadOrg')
        self.user = User.objects.create_superuser(
            username='upload_mut_user',
            email='upload_mut@test.com',
            password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        put_patcher, get_patcher = _patch_presign()
        self.mock_put = put_patcher.start()
        self.mock_get = get_patcher.start()
        self.addCleanup(put_patcher.stop)
        self.addCleanup(get_patcher.stop)

    def _make_context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.user))


# ---------------------------------------------------------------------------
# preSignedUrlImageUpload
# ---------------------------------------------------------------------------

class PreSignedUrlImageUploadTest(UploadMutationTestBase):
    """Tests for the preSignedUrlImageUpload mutation."""

    MUTATION = '''
        mutation PreSign($gid: ID!, $mimetype: String!, $location: UploadLocation,
                         $name: String, $owner: String) {
            preSignedUrlImageUpload(globalId: $gid, mimetype: $mimetype,
                                    location: $location, name: $name,
                                    ownerContainerProperty: $owner) {
                preSignedUrl
                publicUrl
                fileUrl
                uuid
            }
        }
    '''

    def setUp(self):
        super().setUp()
        self.file_upload = FileUpload.objects.create(created_by=self.user)
        self.target_gid = self.file_upload.global_id

    def test_valid_upload_creates_record(self):
        """A valid target creates an Upload row with presigned URLs."""
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={'gid': self.target_gid, 'mimetype': 'image/png'},
            context_value=self._make_context(),
        )
        self.assertIsNone(result.errors)
        data = result.data['preSignedUrlImageUpload']
        self.assertIn('X-Amz-Signature=put-sig', data['preSignedUrl'])
        self.assertEqual(data['publicUrl'], data['fileUrl'])

        upload = Upload.objects.get(id=data['uuid'])
        self.assertEqual(upload.content_type, 'image/png')
        self.assertEqual(upload.target_global_id, self.target_gid)
        self.assertEqual(upload.created_by, self.user)
        self.assertEqual(upload.location, Upload.Location.STATIC.value)
        self.assertTrue(upload.path.endswith('.png'))

    def test_public_location_strips_query_string(self):
        """PUBLIC uploads get a public_url without signing query params."""
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': self.target_gid, 'mimetype': 'image/jpeg', 'location': 'PUBLIC',
            },
            context_value=self._make_context(),
        )
        self.assertIsNone(result.errors)
        data = result.data['preSignedUrlImageUpload']
        self.assertNotIn('?', data['publicUrl'])

        upload = Upload.objects.get(id=data['uuid'])
        self.assertEqual(upload.location, Upload.Location.PUBLIC.value)

    def test_missing_target_errors(self):
        """A global id pointing at a nonexistent entity returns an error."""
        missing_gid = GlobalIDUtils.to_global_id('FileUploadType', 999999)
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={'gid': missing_gid, 'mimetype': 'image/png'},
            context_value=self._make_context(),
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found', str(result.errors[0]))
        self.assertEqual(Upload.objects.count(), 0)

    def test_owner_container_property_foreign_key(self):
        """ownerContainerProperty on a ForeignKey attaches the upload to the owner."""
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': self.target_gid, 'mimetype': 'image/png', 'owner': 'upload',
            },
            context_value=self._make_context(),
        )
        self.assertIsNone(result.errors)
        self.file_upload.refresh_from_db()
        self.assertIsNotNone(self.file_upload.upload_id)
        self.assertEqual(
            str(self.file_upload.upload_id),
            result.data['preSignedUrlImageUpload']['uuid'],
        )

    def test_owner_container_property_shared_directory(self):
        """Uploading into a SharedDirectory M2M creates a SharedFile."""
        directory = SharedDirectory.objects.mkdir(
            path=None, name='Uploads', created_by=self.user,
        )
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': directory.global_id,
                'mimetype': 'application/pdf',
                'owner': 'files',
                'name': 'report.pdf',
            },
            context_value=self._make_context(),
        )
        self.assertIsNone(result.errors)
        shared_file = SharedFile.objects.get(parent=directory)
        self.assertEqual(
            str(shared_file.file_id),
            result.data['preSignedUrlImageUpload']['uuid'],
        )

    def test_owner_container_property_shared_directory_requires_name(self):
        """SharedDirectory uploads without a name are rejected."""
        directory = SharedDirectory.objects.mkdir(
            path=None, name='NoName', created_by=self.user,
        )
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': directory.global_id, 'mimetype': 'application/pdf', 'owner': 'files',
            },
            context_value=self._make_context(),
        )
        self.assertIsNotNone(result.errors)
        self.assertFalse(SharedFile.objects.filter(parent=directory).exists())

    def test_invalid_owner_container_property_errors(self):
        """An ownerContainerProperty that is not a model field errors out."""
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': self.target_gid, 'mimetype': 'image/png', 'owner': 'not_a_field',
            },
            context_value=self._make_context(),
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not a member', str(result.errors[0]))

    def test_anonymous_user_errors(self):
        """An unauthenticated request cannot create uploads."""
        from django.contrib.auth.models import AnonymousUser
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={'gid': self.target_gid, 'mimetype': 'image/png'},
            context_value=self._make_context(AnonymousUser()),
        )
        self.assertIsNotNone(result.errors)
        self.assertEqual(Upload.objects.count(), 0)


# ---------------------------------------------------------------------------
# confirmPreSignedUrlImageUpload
# ---------------------------------------------------------------------------

class ConfirmPreSignedUrlImageUploadTest(UploadMutationTestBase):
    """Tests for the confirmPreSignedUrlImageUpload mutation."""

    MUTATION = '''
        mutation Confirm($publicUrl: String, $uploadId: ID, $metadata: JSON, $delete: Boolean) {
            confirmPreSignedUrlImageUpload(publicUrl: $publicUrl, uploadId: $uploadId,
                                           metadata: $metadata, delete: $delete) {
                ack
            }
        }
    '''

    def setUp(self):
        super().setUp()
        self.upload = Upload.objects.create(
            name='pending.png',
            content_type='image/png',
            public_url='https://s3.test/static/pending.png',
            pre_signed_url='https://s3.test/static/pending.png?sig=put',
            created_by=self.user,
        )

    def _execute(self, variables):
        # The mutation does `from core.schema import UploadType` unconditionally
        # at the top of the resolver, so every execution needs the injected type.
        with _patch_core_schema_types(UploadType=Upload):
            return schema.execute_sync(
                self.MUTATION,
                variable_values=variables,
                context_value=self._make_context(),
            )

    def test_confirm_by_public_url_updates_metadata(self):
        """Confirming by public URL stores metadata and stamps updated_by."""
        result = self._execute({
            'publicUrl': self.upload.public_url,
            'metadata': {'file_name': 'final.png'},
        })
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['confirmPreSignedUrlImageUpload']['ack'])

        self.upload.refresh_from_db()
        self.assertEqual(self.upload.metadata, {'file_name': 'final.png'})
        self.assertEqual(self.upload.updated_by, self.user)
        self.assertIsNone(self.upload.deleted_at)

    def test_confirm_by_upload_id(self):
        """Confirming by relay upload id resolves the same record."""
        result = self._execute({
            'uploadId': self.upload.global_id,
            'metadata': {'confirmed': True},
        })
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['confirmPreSignedUrlImageUpload']['ack'])
        self.upload.refresh_from_db()
        self.assertEqual(self.upload.metadata, {'confirmed': True})

    def test_confirm_with_delete_soft_deletes(self):
        """delete=true soft-deletes the upload (row stays, deleted_at/by set)."""
        result = self._execute({'publicUrl': self.upload.public_url, 'delete': True})
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['confirmPreSignedUrlImageUpload']['ack'])

        self.upload.refresh_from_db()
        self.assertIsNotNone(self.upload.deleted_at)
        self.assertEqual(self.upload.deleted_by, self.user)
        self.assertTrue(Upload.objects.filter(pk=self.upload.pk).exists())

    def test_confirm_without_id_or_url_errors(self):
        """Passing neither uploadId nor publicUrl is rejected."""
        result = self._execute({'metadata': {'x': 1}})
        self.assertIsNotNone(result.errors)
        self.assertIn('Requires either an upload id or a public URL', str(result.errors[0]))

    def test_confirm_unknown_public_url_errors(self):
        """A public URL that matches no upload errors out."""
        result = self._execute({'publicUrl': 'https://s3.test/static/ghost.png'})
        self.assertIsNotNone(result.errors)


# ---------------------------------------------------------------------------
# fileUpload
# ---------------------------------------------------------------------------

class FileUploadMutationTest(UploadMutationTestBase):
    """Tests for the fileUpload mutation."""

    MUTATION = '''
        mutation FileUp($mimetype: String!, $gid: ID, $name: String,
                        $description: String, $isPublic: Boolean) {
            fileUpload(mimetype: $mimetype, fileUploadGid: $gid, name: $name,
                       description: $description, isPublic: $isPublic) {
                id
                preSignedUrl
                publicUrl
            }
        }
    '''

    def _execute(self, variables):
        # The mutation imports FileUploadType from the legacy core.schema.upload
        # module path; inject it so the code under test can resolve objects.
        fake_module = types.ModuleType('core.schema.upload')
        fake_module.FileUploadType = types.SimpleNamespace(
            get_object=staticmethod(_fake_get_object(FileUpload)),
        )
        with patch.dict(sys.modules, {'core.schema.upload': fake_module}):
            return schema.execute_sync(
                self.MUTATION,
                variable_values=variables,
                context_value=self._make_context(),
            )

    def test_file_upload_creates_wrapper_and_upload(self):
        """Without a gid, a new FileUpload wrapper is created and wired to the Upload."""
        result = self._execute({'mimetype': 'application/pdf', 'name': 'contract.pdf'})
        self.assertIsNone(result.errors)

        # The Upload post_save signal auto-creates a second (unattributed) wrapper;
        # the mutation's own wrapper is the one stamped with created_by.
        file_upload = FileUpload.objects.get(created_by=self.user)
        self.assertIsNotNone(file_upload.upload)
        self.assertEqual(file_upload.upload.content_type, 'application/pdf')
        self.assertEqual(file_upload.upload.name, 'contract.pdf')
        self.assertEqual(file_upload.created_by, self.user)
        self.assertEqual(file_upload.upload.location, Upload.Location.STATIC.value)
        self.assertEqual(result.data['fileUpload']['id'], file_upload.upload.global_id)

    def test_file_upload_existing_gid_reuses_wrapper(self):
        """With a gid, the existing FileUpload wrapper is reused (no new user-attributed wrapper)."""
        existing = FileUpload.objects.create(created_by=self.user)
        result = self._execute({
            'mimetype': 'text/plain', 'gid': existing.global_id,
        })
        self.assertIsNone(result.errors)
        # Only the signal-created wrapper is added; the mutation reuses `existing`.
        self.assertEqual(FileUpload.objects.filter(created_by=self.user).count(), 1)
        existing.refresh_from_db()
        self.assertIsNotNone(existing.upload)
        self.assertEqual(existing.upload.content_type, 'text/plain')

    def test_file_upload_is_public(self):
        """isPublic stores the upload in the PUBLIC location."""
        result = self._execute({'mimetype': 'image/png', 'isPublic': True})
        self.assertIsNone(result.errors)
        upload = FileUpload.objects.get(created_by=self.user).upload
        self.assertEqual(upload.location, Upload.Location.PUBLIC.value)
        self.assertNotIn('?', result.data['fileUpload']['publicUrl'])


# ---------------------------------------------------------------------------
# processFile
# ---------------------------------------------------------------------------

class ProcessFileMutationTest(UploadMutationTestBase):
    """Tests for the processFile mutation (AwsProcessSystem mocked)."""

    MUTATION = '''
        mutation Process($entityType: EntityType!, $fileId: ID!, $processId: ID) {
            processFile(entityType: $entityType, uploadedFileId: $fileId, processId: $processId) {
                processId
                status
                errors
                successful
            }
        }
    '''

    def setUp(self):
        super().setUp()
        self.upload = Upload.objects.create(
            name='import.csv',
            content_type='text/csv',
            public_url='https://s3.test/static/import.csv',
            pre_signed_url='https://s3.test/static/import.csv?sig=put',
            path='static/import.csv',
            created_by=self.user,
        )
        self.process = DataProcess.objects.create(
            file_type=FileType.CSV,
            entity_type=EntityType.EMPLOYEE,
            uploaded_file=self.upload,
            created_by=self.user,
        )
        DataProcessEntity.objects.create(
            process=self.process, line_number=1,
            status=ProcessStatus.DONE, created_by=self.user,
        )
        DataProcessEntity.objects.create(
            process=self.process, line_number=2,
            status=ProcessStatus.DONE, created_by=self.user,
        )
        DataProcessEntity.objects.create(
            process=self.process, line_number=3,
            status=ProcessStatus.FAILED, created_by=self.user,
        )

    def _execute(self, variables):
        fake_process_module = types.ModuleType('core.schema.process')
        fake_process_module.DataProcessType = types.SimpleNamespace(
            get_object=staticmethod(_fake_get_object(DataProcess)),
        )
        get_as_object = patch.object(
            Upload, 'get_as_object',
            return_value={'Body': b'a,b\n1,2\n', 'ContentType': 'text/csv'},
        )

        def fake_process(process, user, *args, **kwargs):
            process.update_status(ProcessStatus.DONE)
            return process

        aws = patch('core.schema.mutations.upload.AwsProcessSystem')
        with _patch_core_schema_types(UploadType=Upload), \
                patch.dict(sys.modules, {'core.schema.process': fake_process_module}), \
                get_as_object, aws as mock_aws:
            mock_aws.load_file_data.return_value = self.process
            mock_aws.process.side_effect = fake_process
            result = schema.execute_sync(
                self.MUTATION,
                variable_values=variables,
                context_value=self._make_context(),
            )
        return result, mock_aws

    def test_process_file_loads_and_processes(self):
        """Without processId the file is loaded then processed; counts are reported."""
        result, mock_aws = self._execute({
            'entityType': 'EMPLOYEE', 'fileId': self.upload.global_id,
        })
        self.assertIsNone(result.errors)
        data = result.data['processFile']
        self.assertEqual(data['processId'], self.process.global_id)
        self.assertEqual(data['status'], ProcessStatus.DONE)
        self.assertEqual(data['errors'], 1)
        self.assertEqual(data['successful'], 2)
        mock_aws.load_file_data.assert_called_once()
        mock_aws.process.assert_called_once()

    def test_process_file_with_existing_process_id(self):
        """With processId the existing process is reused (no reload from S3)."""
        result, mock_aws = self._execute({
            'entityType': 'EMPLOYEE',
            'fileId': self.upload.global_id,
            'processId': self.process.global_id,
        })
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['processFile']['processId'], self.process.global_id)
        mock_aws.load_file_data.assert_not_called()
        mock_aws.process.assert_called_once()


# ---------------------------------------------------------------------------
# profileImageFieldUpload
# ---------------------------------------------------------------------------

class ProfileImageFieldUploadTest(UploadMutationTestBase):
    """Tests for the profileImageFieldUpload mutation (avatar/signature flows)."""

    MUTATION = '''
        mutation ProfileImg($gid: ID!, $mimetype: String!, $field: ProfileImageField) {
            profileImageFieldUpload(globalId: $gid, mimetype: $mimetype, field: $field) {
                upload {
                    contentType
                }
            }
        }
    '''

    def setUp(self):
        super().setUp()
        self.profile = self.user.profile
        self.profile_gid = self.profile.global_id

    def test_avatar_whitelisted_skips_approval_flow(self):
        """A whitelisted field saves the upload directly on the profile."""
        # Ensure the draft exists — the direct-save path writes to profile.draft.
        # NOTE: get_draft mutates the instance passed in (it becomes the draft
        # row), so always work from the returned (original, draft) tuple.
        original, draft = Profile.objects.get_draft(self.profile)
        with patch.object(Profile, 'whitelist_fields', classmethod(lambda cls: ['avatar'])):
            result = schema.execute_sync(
                self.MUTATION,
                variable_values={
                    'gid': self.profile_gid, 'mimetype': 'image/png', 'field': 'AVATAR',
                },
                context_value=self._make_context(),
            )
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['profileImageFieldUpload']['upload']['contentType'], 'image/png',
        )
        original.refresh_from_db()
        self.assertIsNotNone(original.avatar)
        self.assertEqual(original.avatar.location, Upload.Location.PUBLIC.value)
        # The draft mirrors the published avatar
        draft.refresh_from_db()
        self.assertEqual(draft.avatar_id, original.avatar_id)

    def test_signature_non_whitelisted_goes_to_draft(self):
        """A non-whitelisted field writes to the draft profile, not the original."""
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'gid': self.profile_gid, 'mimetype': 'image/png', 'field': 'SIGNATURE',
            },
            context_value=self._make_context(),
        )
        self.assertIsNone(result.errors)

        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.signature_id)

        draft = Profile.objects.filter(parent=self.profile).get()
        self.assertIsNotNone(draft.signature_id)
        self.assertEqual(draft.document_option, Profile.DocumentOptions.DRAFTED)

    def test_existing_upload_with_same_mimetype_is_reused(self):
        """Re-uploading the same field with the same mimetype updates the existing Upload."""
        Profile.objects.get_draft(self.profile)
        with patch.object(Profile, 'whitelist_fields', classmethod(lambda cls: ['avatar'])):
            context = self._make_context()
            schema.execute_sync(
                self.MUTATION,
                variable_values={
                    'gid': self.profile_gid, 'mimetype': 'image/png', 'field': 'AVATAR',
                },
                context_value=context,
            )
            self.profile.refresh_from_db()
            first_avatar_id = self.profile.avatar_id

            schema.execute_sync(
                self.MUTATION,
                variable_values={
                    'gid': self.profile_gid, 'mimetype': 'image/png', 'field': 'AVATAR',
                },
                context_value=context,
            )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar_id, first_avatar_id)


# ---------------------------------------------------------------------------
# FileUpload.id regression (see #107 checkpoint)
# ---------------------------------------------------------------------------

class FileUploadIdRegressionTest(TestCase):
    """FileUpload.id must be the auto pk, with the relay id on global_id.

    A class-body `id` property (returning global_id) used to shadow the pk in
    the source; Django installs the pk descriptor after the class body runs,
    so the property was silently dead. This locks in the real contract.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='fileupload_id_user', email='fid@test.com', password='x',
        )
        self.file_upload = FileUpload.objects.create(created_by=self.user)

    def test_id_is_integer_pk(self):
        """`.id` is the concrete auto pk, not a relay global id."""
        self.assertEqual(self.file_upload.id, self.file_upload.pk)
        self.assertIsInstance(self.file_upload.id, int)

    def test_global_id_encodes_type_and_pk(self):
        """`.global_id` round-trips to (FileUploadType, pk)."""
        type_name, pk = GlobalIDUtils.from_global_id(self.file_upload.global_id)
        self.assertEqual(type_name, 'FileUploadType')
        self.assertEqual(int(pk), self.file_upload.pk)

    def test_no_id_property_on_class(self):
        """The pk descriptor owns `id`; no property may shadow (or be shadowed by) it."""
        self.assertNotIsInstance(FileUpload.__dict__.get('id'), property)
        self.assertEqual(FileUpload._meta.pk.attname, 'id')
