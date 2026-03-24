import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID, uuid4

import graphene
from core.models import SharedDirectory, SharedFile
from core.models.process import DataProcessEntity, EntityType, FileType, ProcessStatus
from core.models.upload import FileUpload, Upload
from core.schema import DjangoObjectTypeUtils
from core.schema.process import DataProcessType
from core.systems import AwsProcessSystem
from django.contrib.contenttypes.models import ContentType
from graphene_django.registry import get_global_registry

# Optional import - Domain-specific functionality
try:
    from domain_app.models import Employee
    HAS_DOMAIN_APP = True
except ImportError:
    Employee = None
    HAS_DOMAIN_APP = False
from graphql import GraphQLError
from graphql_relay import from_global_id
from organization.models import Organization

logger = logging.getLogger(__name__)
UploadLocation = graphene.Enum.from_enum(Upload.Location)


class PreSignedUrlImageUploadMutation(graphene.Mutation, DjangoObjectTypeUtils):
    class Arguments:

        global_id = graphene.ID(
            required=True,
            description='Global ID of the entity the file belongs to.',
        )

        mimetype = graphene.String(
            required=True,
            description='Content Type of the object to be uploaded.',
        )

        uuid = graphene.UUID(
            required=False,
            description='Unique identifier of the upload, it is optional. If provided the file will be replaced',
        )

        metadata = graphene.JSONString(
            required=False,
            description='Additional metadata about the file uploaded.',
        )

        location = graphene.Argument(
            UploadLocation,
            description='File location, by default it will used the static (private) media location.',
        )

        description = graphene.String(
            required=False,
            description='Description of the file.'
        )

        name = graphene.String(
            required=False,
            description='User friendly name of the file.'
        )

        owner_container_property = graphene.String(
            required=False,
            description='Name of the property/attribute the file will use to be attach/link to the owner entity.'
                        'I.E. For the Profile entity, the properties avatar and signature are eligible.'
        )

    pre_signed_url = graphene.String(
        description='Pre-signed URL of the file, use it to upload the '
                    'data directly to the bucket.'
    )

    public_url = graphene.String(
        description='Deprecated: Public URL of the upload within the storage system.'
    )

    file_url = graphene.String(
        description='URL of the file within the storage system. Static urls will be preSigned and expire at one point.'
    )

    uuid = graphene.UUID(
        description='Unique identifier of the upload'
    )

    @classmethod
    def _exists_global_id_guard(cls, info, global_id: str) -> Tuple[str, str]:
        model_name, pk = from_global_id(global_id)
        r = get_global_registry()
        for model, g_type in r._registry.items():
            if str(g_type) == model_name:
                # Raise an exception if the object referenced by the global id
                # does not exist.
                g_type.get_object(info, global_id, raise_not_found=True)
                break
        return model_name, pk

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            global_id: str,
            mimetype: str,
            owner_container_property: str = None,
            name=None,
            uuid: Optional[UUID] = None,
            location: Optional[Upload.Location] = None,
            metadata: Optional[dict] = None,
            **kwargs):
        """
        Provides a pre-signed url for uploading images and some other files
        """
        upload = cls.create_upload(
            info,
            global_id,
            mimetype,
            uuid=uuid,
            location=location,
            metadata=metadata,
            name=name,
        )

        model_name, pk = from_global_id(global_id)
        model_name: str = model_name.replace('Type', '').lower()

        ct = ContentType.objects.get(model=model_name)
        model = ct.model_class()

        if owner_container_property:
            if not hasattr(model, owner_container_property):
                raise ValueError(f'Property {owner_container_property} is not a member of type {model_name}')

            match type(model._meta.get_field(owner_container_property)).__name__:
                case "ManyToManyField" if model is SharedDirectory:
                    if name is None:
                        raise ValueError(f'Property {name} is required uploading a file to Shared Directory')
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
                    raise ValueError(f'Created upload cannot be attach to target property {owner_container_property}')

        return PreSignedUrlImageUploadMutation(
            public_url=upload.public_url,
            file_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url,
            uuid=upload.id
        )

    @classmethod
    def create_upload(
            cls,
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
        cls._exists_global_id_guard(info, global_id)
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


class ConfirmPreSignedUrlImageUploadMutation(graphene.Mutation, DjangoObjectTypeUtils):

    class Arguments:
        public_url = graphene.String(
            description='Public URL of the image.'
        )

        metadata = graphene.JSONString(
            required=False,
            description='Additional metadata about the file uploaded.',
        )

        delete = graphene.Boolean(
            required=False,
            description='Set to true to make the file inaccessible. This is a one time operation',
        )

        upload_id = graphene.ID(
            required=False,
            description='ID of the upload to be confirmed/updated'
        )

        expiration_date = graphene.Date(
            required=False,
            description='Use for documents that have an expiration date, such as driving licenses. Format YYYY-MM-DD')

    ack = graphene.Boolean(description="Acknowledges the image upload and/or update.")

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            public_url: str,
            metadata: Optional[dict] = None,
            delete: Optional[bool] = None,
            upload_id: Optional[str] = None,
            **kwargs
    ):
        from core.schema import UploadType
        if not upload_id and not public_url:
            raise GraphQLError('Requires either an upload id or a public URL to complete the update/confirmation.')
        upload = UploadType.get_object(info, global_id=upload_id, raise_not_found=True) \
            if upload_id \
            else Upload.objects.filter(public_url=public_url).get()
        upload.updated_by = info.context.user
        upload.updated_at = datetime.now()
        upload.metadata = metadata or upload.metadata
        if 'expiration_date' in kwargs:
            upload.employee_document_upload.update(expiration_date=kwargs['expiration_date'])
        if delete:
            upload.deleted_by = info.context.user
            upload.deleted_at = datetime.now()
            logger.info(f'Marking upload with id {upload.id} as deleted')
        upload.save()
        return ConfirmPreSignedUrlImageUploadMutation(ack=True)


class DataImportFileUploadMutation(graphene.Mutation):
    class Arguments:
        mimetype = graphene.String(
            required=True,
            description='Content Type of the object to be uploaded.',
        )

        metadata = graphene.JSONString(
            required=False,
            description='Additional metadata about the file uploaded.',
        )

    pre_signed_url = graphene.String(
        description='Pre-signed URL of the file, use it to upload the '
                    'data directly to the bucket.'
    )

    public_url = graphene.String(
        description='Public URL of the text file.'
    )

    id = graphene.ID(
        description='Unique identifier of the upload'
    )

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            mimetype: str,
            metadata: Optional[dict] = None,
            **kwargs):
        if mimetype not in FileType.labels:
            raise GraphQLError('Invalid mimetype, must be one of {}'.format(', '.join(FileType.labels)))

        if not HAS_DOMAIN_APP:
            raise GraphQLError('Data import feature requires domain app')

        employee: Employee = Employee.objects.filter(membership__member_id=info.context.user.id,
                                                     membership__is_active=True).first()

        if not employee:
            raise GraphQLError('No active employee found for current user')

        upload = PreSignedUrlImageUploadMutation.create_upload(
            info=info,
            global_id=employee.global_id(),
            mimetype=mimetype,
            location=Upload.Location.STATIC,
            metadata=metadata,
        )
        employee.import_process_documents.add(upload.id)
        employee.save()
        return DataImportFileUploadMutation(
            public_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url,
            id=upload.global_id
        )


class ProcessFileMutation(graphene.Mutation):
    class Arguments:
        entity_type = graphene.Argument(graphene.Enum.from_enum(EntityType), required=True)
        process_id = graphene.ID(description='Unique identifier of the processing record. Required for retrying rows.')
        uploaded_file_id = graphene.ID(description='Unique identifier of the uploaded file', required=True)

    errors = graphene.Int(description="Number of individual errors encountered.")
    process_id = graphene.ID(description='Unique identifier of the processing record.')
    successful = graphene.Int(description="Number of file lines processed correctly.")
    status = graphene.String(description="Overall result of the processing task.")

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            entity_type: EntityType,
            uploaded_file_id: str,
            process_id: str = None,
            **kwargs):
        from core.schema import UploadType
        upload: Upload = UploadType.get_object(info, uploaded_file_id, raise_not_found=True)
        obj = upload.get_as_object()
        if process_id:
            process = DataProcessType.get_object(info, process_id, raise_not_found=True)
        else:
            process = AwsProcessSystem.load_file_data(obj, upload.id, entity_type=entity_type)
        process = AwsProcessSystem.process(process, info.context.user)
        error_count = DataProcessEntity.objects.filter(process=process, status__exact=ProcessStatus.FAILED).count()
        success_count = DataProcessEntity.objects.filter(process=process, status__exact=ProcessStatus.DONE).count()
        return ProcessFileMutation(process_id=process.global_id,
                                   status=process.status,
                                   errors=error_count,
                                   successful=success_count)


class FileUploadMutation(graphene.Mutation):
    class Arguments:
        file_upload_gid = graphene.ID(
            description='Unique identifier of the file upload. If exists, the file will be replaced with the new one.',
            required=False
        )
        mimetype = graphene.String(
            required=True,
            description='Content Type of the object to be uploaded.',
        )

        metadata = graphene.JSONString(
            required=False,
            description='Additional metadata about the file uploaded.',
        )
        name = graphene.String(
            required=False,
            description='User friendly name of the file.'
        )
        description = graphene.String(
            required=False,
            description='Description of the file.'
        )
        is_public = graphene.Boolean(required=False, description='Set to true if the file is public.')

    pre_signed_url = graphene.String(
        description='Pre-signed URL of the file, use it to upload the '
                    'data directly to the bucket.'
    )

    public_url = graphene.String(
        description='Public URL of the text file.'
    )

    id = graphene.ID(
        description='Unique identifier of the upload'
    )

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            mimetype: str,
            file_upload_gid: Optional[str] = None,
            metadata: Optional[dict] = None,
            name=None,
            description=None,
            is_public=False,
            **kwargs):

        from core.schema.upload import FileUploadType
        if file_upload_gid:
            file_upload = FileUploadType.get_object(info, file_upload_gid, raise_not_found=True)
        else:
            file_upload = FileUpload.objects.create(
                created_by=info.context.user,
            )
            file_upload_gid = file_upload.global_id

        upload = PreSignedUrlImageUploadMutation.create_upload(
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

        return cls(
            id=upload.global_id,
            public_url=upload.public_url,
            pre_signed_url=upload.pre_signed_url
        )
