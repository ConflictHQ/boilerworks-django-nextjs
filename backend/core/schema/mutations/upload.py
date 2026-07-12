"""Upload mutations migrated from Graphene to Strawberry.

Includes PreSignedUrlImageUploadMutation, ConfirmPreSignedUrlImageUploadMutation,
DataImportFileUploadMutation, ProcessFileMutation, FileUploadMutation,
and ProfileImageFieldUploadMutation.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4

import strawberry
from core.models import Profile, SharedDirectory, SharedFile
from core.models.process import DataProcessEntity, EntityType, FileType, ProcessStatus
from core.models.upload import FileUpload, Upload
from core.schema.common import GlobalIDUtils
from core.schema.types.upload import UploadType as StrawberryUploadType
from core.systems import AwsProcessSystem
from django.contrib.contenttypes.models import ContentType
from graphql import GraphQLError
from strawberry.types import Info

# Optional import - Domain-specific functionality
try:
    from domain_app.models import Employee
    HAS_DOMAIN_APP = True
except ImportError:
    Employee = None
    HAS_DOMAIN_APP = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

UploadLocationEnum = strawberry.enum(Upload.Location, name="UploadLocation")
EntityTypeEnum = strawberry.enum(EntityType, name="EntityType")
ProfileImageFieldEnum = strawberry.enum(Profile.ImageField, name="ProfileImageField")


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@strawberry.type
class PreSignedUrlUploadResult:
    pre_signed_url: Optional[str] = None
    public_url: Optional[str] = None
    file_url: Optional[str] = None
    uuid: Optional[UUID] = None


@strawberry.type
class ConfirmUploadResult:
    ack: bool


@strawberry.type
class DataImportUploadResult:
    pre_signed_url: Optional[str] = None
    public_url: Optional[str] = None
    id: Optional[strawberry.ID] = None


@strawberry.type
class ProcessFileResult:
    errors: Optional[int] = None
    process_id: Optional[strawberry.ID] = None
    successful: Optional[int] = None
    status: Optional[str] = None


@strawberry.type
class FileUploadResult:
    pre_signed_url: Optional[str] = None
    public_url: Optional[str] = None
    id: Optional[strawberry.ID] = None


@strawberry.type
class ProfileImageFieldUploadResult:
    upload: Optional[StrawberryUploadType] = None


# ---------------------------------------------------------------------------
# Shared create_upload helper (mirrors PreSignedUrlImageUploadMutation.create_upload)
# ---------------------------------------------------------------------------

def _exists_global_id_guard(info, global_id: str):
    """Ensure the entity referenced by global_id exists."""
    type_name, pk = GlobalIDUtils.from_global_id(global_id)
    GlobalIDUtils.find_object_by_global_id(global_id, raise_not_found=True)
    return type_name, pk


def create_upload(
    info,
    global_id: str,
    mimetype: str,
    uuid: Optional[UUID] = None,
    location: Optional[Upload.Location] = None,
    metadata: Optional[dict] = None,
    upload: Optional[Upload] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Upload:
    """Create or update an Upload record and generate pre-signed URLs.

    This mirrors PreSignedUrlImageUploadMutation.create_upload exactly.
    """
    _exists_global_id_guard(info, global_id)
    from organization.models import Organization
    organization: Organization = info.context.user.profile.organization()
    upload_location: Upload.Location = location and Upload.Location(location) or Upload.Location.STATIC
    uuid = uuid or (upload and upload.id) or uuid4()
    path = Upload.generate_path(
        upload_location,
        organization=organization,
        target_global_id=global_id,
        uuid=uuid,
        mimetype=mimetype,
    )
    public_url = Upload.generate_pre_signed_url_for_get(path, content_type=mimetype)
    if upload_location == Upload.Location.PUBLIC:
        public_url = public_url.split('?')[0]
    if upload is None:
        pre_signed_url = Upload.generate_pre_signed_url_for_put(path, content_type=mimetype)
        upload, _created = Upload.objects.update_or_create(
            id=uuid,
            defaults=dict(
                pre_signed_url=pre_signed_url,
                public_url=public_url,
                content_type=mimetype,
                target_global_id=global_id,
                created_by=info.context.user,
                metadata=metadata,
                location=upload_location.value,
                path=path,
                name=name,
                description=description,
            )
        )
    else:
        upload.metadata = metadata
        upload.save()
    return upload


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@strawberry.type
class UploadMutations:

    @strawberry.mutation(
        description="Get a pre-signed URL for uploading an image or file. "
                    "Optionally attach it to an entity via owner_container_property."
    )
    def pre_signed_url_image_upload(
        self,
        info: Info,
        global_id: strawberry.ID,
        mimetype: str,
        uuid: Optional[UUID] = None,
        metadata: Optional[strawberry.scalars.JSON] = None,
        location: Optional[UploadLocationEnum] = None,
        description: Optional[str] = None,
        name: Optional[str] = None,
        owner_container_property: Optional[str] = None,
    ) -> PreSignedUrlUploadResult:
        upload = create_upload(
            info,
            global_id,
            mimetype,
            uuid=uuid,
            location=location,
            metadata=metadata,
            name=name,
        )

        model_name, pk = GlobalIDUtils.from_global_id(global_id)
        model_name_lower: str = model_name.replace('Type', '').lower()

        ct = ContentType.objects.get(model=model_name_lower)
        model = ct.model_class()

        if owner_container_property:
            if not hasattr(model, owner_container_property):
                raise ValueError(
                    f'Property {owner_container_property} is not a member of type {model_name_lower}'
                )

            match type(model._meta.get_field(owner_container_property)).__name__:
                case "ManyToManyField" if model is SharedDirectory:
                    if name is None:
                        raise ValueError(
                            f'Property {name} is required uploading a file to Shared Directory'
                        )
                    shared_directory: SharedDirectory = model.objects.filter(pk=pk).first()
                    shared_file = SharedFile(
                        file=upload,
                        parent=shared_directory,
                        created_by=info.context.user,
                    )
                    shared_file.clean()
                    shared_file.save()
                case "ManyToManyField":
                    owner_model = model.objects.filter(pk=pk).first()
                    target_property = getattr(owner_model, owner_container_property)
                    target_property.add(upload.id)
                    owner_model.save()
                case "ForeignKey":
                    owner_model = model.objects.filter(pk=pk).first()
                    setattr(owner_model, owner_container_property + '_id', upload.id)
                    owner_model.save()
                case _:
                    raise ValueError(
                        f'Created upload cannot be attach to target property {owner_container_property}'
                    )

        return PreSignedUrlUploadResult(
            public_url=upload.public_url,
            file_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url,
            uuid=upload.id,
        )

    @strawberry.mutation(
        description="Confirm or update a previously uploaded file. "
                    "Set delete=true to soft-delete the upload."
    )
    def confirm_pre_signed_url_image_upload(
        self,
        info: Info,
        public_url: Optional[str] = None,
        metadata: Optional[strawberry.scalars.JSON] = None,
        delete: Optional[bool] = None,
        upload_id: Optional[strawberry.ID] = None,
        expiration_date: Optional[date] = None,
    ) -> ConfirmUploadResult:
        from core.schema import UploadType

        if not upload_id and not public_url:
            raise GraphQLError(
                'Requires either an upload id or a public URL to complete the update/confirmation.'
            )
        if upload_id:
            upload = UploadType.get_object(info, global_id=upload_id, raise_not_found=True)
        else:
            upload = Upload.objects.filter(public_url=public_url).get()

        upload.updated_by = info.context.user
        upload.updated_at = datetime.now()
        upload.metadata = metadata or upload.metadata

        if expiration_date is not None:
            upload.employee_document_upload.update(expiration_date=expiration_date)
        if delete:
            upload.deleted_by = info.context.user
            upload.deleted_at = datetime.now()
            logger.info(f'Marking upload with id {upload.id} as deleted')

        upload.save()
        return ConfirmUploadResult(ack=True)

    @strawberry.mutation(description="Upload a data import file and get a pre-signed URL.")
    def upload_text_file(
        self,
        info: Info,
        mimetype: str,
        metadata: Optional[strawberry.scalars.JSON] = None,
    ) -> DataImportUploadResult:
        if mimetype not in FileType.labels:
            raise GraphQLError(
                'Invalid mimetype, must be one of {}'.format(', '.join(FileType.labels))
            )

        if not HAS_DOMAIN_APP:
            raise GraphQLError('Data import feature requires domain app')

        employee: Employee = Employee.objects.filter(
            membership__member_id=info.context.user.id,
            membership__is_active=True,
        ).first()

        if not employee:
            raise GraphQLError('No active employee found for current user')

        upload = create_upload(
            info=info,
            global_id=employee.global_id(),
            mimetype=mimetype,
            location=Upload.Location.STATIC,
            metadata=metadata,
        )
        employee.import_process_documents.add(upload.id)
        employee.save()

        return DataImportUploadResult(
            public_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url,
            id=upload.global_id,
        )

    @strawberry.mutation(description="Process a previously uploaded data import file.")
    def process_file(
        self,
        info: Info,
        entity_type: EntityTypeEnum,
        uploaded_file_id: strawberry.ID,
        process_id: Optional[strawberry.ID] = None,
    ) -> ProcessFileResult:
        from core.schema import UploadType
        from core.schema.process import DataProcessType

        upload: Upload = UploadType.get_object(info, uploaded_file_id, raise_not_found=True)
        obj = upload.get_as_object()

        if process_id:
            process = DataProcessType.get_object(info, process_id, raise_not_found=True)
        else:
            process = AwsProcessSystem.load_file_data(obj, upload.id, entity_type=entity_type)

        process = AwsProcessSystem.process(process, info.context.user)
        error_count = DataProcessEntity.objects.filter(
            process=process, status__exact=ProcessStatus.FAILED,
        ).count()
        success_count = DataProcessEntity.objects.filter(
            process=process, status__exact=ProcessStatus.DONE,
        ).count()

        return ProcessFileResult(
            process_id=process.global_id,
            status=process.status,
            errors=error_count,
            successful=success_count,
        )

    @strawberry.mutation(
        description="Upload a file and get a pre-signed URL. "
                    "Creates a FileUpload wrapper around the Upload."
    )
    def file_upload(
        self,
        info: Info,
        mimetype: str,
        file_upload_gid: Optional[strawberry.ID] = None,
        metadata: Optional[strawberry.scalars.JSON] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = False,
    ) -> FileUploadResult:
        from core.schema.upload import FileUploadType

        if file_upload_gid:
            file_upload = FileUploadType.get_object(info, file_upload_gid, raise_not_found=True)
        else:
            file_upload = FileUpload.objects.create(
                created_by=info.context.user,
            )
            file_upload_gid = file_upload.global_id

        upload = create_upload(
            info=info,
            global_id=file_upload_gid,
            mimetype=mimetype,
            location=Upload.Location.PUBLIC if is_public else Upload.Location.STATIC,
            metadata=metadata,
            name=name,
            description=description,
        )

        file_upload.upload = upload
        file_upload.save()

        return FileUploadResult(
            id=upload.global_id,
            public_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url,
        )

    @strawberry.mutation(
        description="Upload an image for a specific profile image field (avatar, signature). "
                    "Supports the approval request workflow for non-whitelisted fields."
    )
    def profile_image_field_upload(
        self,
        info: Info,
        global_id: strawberry.ID,
        mimetype: str,
        field: Optional[ProfileImageFieldEnum] = None,
        metadata: Optional[strawberry.scalars.JSON] = None,
    ) -> ProfileImageFieldUploadResult:
        # Optional import - Domain-specific functionality
        try:
            from domain_app.models import ApprovalRequest
            has_domain_app = True
        except ImportError:
            ApprovalRequest = None
            has_domain_app = False

        from config.roles_gen import P

        model_name, pk = GlobalIDUtils.from_global_id(global_id)
        assert model_name != Profile._meta.model_name
        profile_original: Profile = Profile.objects.get(pk=pk)
        whitelist: List[str] = Profile.whitelist_fields()

        if field.value in whitelist:
            # Skip approval request flow
            # NOTE: strawberry passes root=None as `self` for root-level mutations,
            # so the helper must be referenced via the class, not `self`.
            return ProfileImageFieldUploadResult(
                upload=UploadMutations._save_profile_upload(
                    field, global_id, info, metadata, mimetype, profile_original,
                )
            )

        original, draft = Profile.objects.get_draft(profile_original)

        if has_domain_app:
            with ApprovalRequest.objects.for_instance(
                    instance=draft,
                    permission=P.PROFILE_APPROVE_CHANGES.perm(),
                    created_by=info.context.user,
            ):
                profile = draft
                profile.document_option = Profile.DocumentOptions.DRAFTED
                upload = UploadMutations._save_profile_upload(
                    field, global_id, info, metadata, mimetype, profile,
                )
        else:
            profile = draft
            upload = UploadMutations._save_profile_upload(
                field, global_id, info, metadata, mimetype, profile,
            )

        return ProfileImageFieldUploadResult(upload=upload)

    @staticmethod
    def _save_profile_upload(field, global_id, info, metadata, mimetype, profile):
        """Save an upload for a profile image field (avatar or signature)."""
        existing_upload: Optional[Upload] = None
        match field:
            case Profile.ImageField.AVATAR:
                existing_upload = profile.avatar
            case Profile.ImageField.SIGNATURE:
                existing_upload = profile.signature

        if existing_upload and existing_upload.content_type != mimetype:
            existing_upload = None

        upload = create_upload(
            info=info,
            global_id=global_id,
            mimetype=mimetype,
            location=Upload.Location.PUBLIC,
            metadata=metadata,
            upload=existing_upload,
        )

        match field:
            case Profile.ImageField.AVATAR:
                profile.avatar = upload
                if profile.user_id:
                    profile.draft.avatar = upload
            case Profile.ImageField.SIGNATURE:
                profile.signature = upload
                if profile.user_id:
                    profile.draft.signature = upload

        profile.save()
        if profile.user_id:
            profile.draft.save()

        return upload
