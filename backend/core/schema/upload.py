import graphene
from core.models import Upload
from core.models.upload import FileUpload, UploadQuerySet
from core.schema import CaseInsensitiveOrderingFilter, DjangoObjectTypeUtils, DjangoPermissionFilterMixin, MetaNode
from django.contrib.auth.models import User
from django_filters import FilterSet
from graphene_django import DjangoObjectType


class UploadFilter(FilterSet):
    order_by = CaseInsensitiveOrderingFilter(
        fields=dict(
            name='name',
        )
    )

    class Meta:
        model = Upload
        fields = (
            'id',
            'content_type',
            'created_by',
            'updated_by',
            'location',
        )

    def __init__(self, *args, **kwargs):
        if 'data' in kwargs and ('order_by' not in kwargs['data'] or kwargs['data']['order_by'] is None):
            kwargs['data']['order_by'] = 'name'
        super(UploadFilter, self).__init__(*args, **kwargs)


class UploadType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    target_global_id = graphene.String(
        source='target_global_id',
        description='Global ID of the target object.',
        required=True
    )

    class Meta(MetaNode):
        model = Upload
        filter_class = UploadFilter
        fields = (
            'id',
            'name',
            'description',
            'content_type',
            'created_by',
            'updated_by',
            'deleted_by',
            'metadata',
            'created_at',
            'updated_at',
            'deleted_at',
            'target_global_id',
            'location',
            'pre_signed_url',
        )

    public_transient_url = graphene.String(
        description='Deprecated. Public URL for image, it is temporary.'
    )

    public_permanent_url = graphene.String(
        description='Deprecated: Public URL for image, it is temporary.',
    )

    file_url = graphene.String(
        description='URL of the file within the storage system. Static files will be presigned and expire at one point.'
    )

    @classmethod
    def get_queryset(cls, queryset: UploadQuerySet, info):
        return queryset.with_view_permission_info(info).filter(deleted_at__isnull=True)

    @classmethod
    def resolve_public_transient_url(cls, root: Upload, info, **kwargs):
        # Fixme # Core.DataProcessEntity
        organization = info.context.user.profile.organization()
        path = Upload.generate_path(
            location=Upload.Location(root.location),
            organization=organization,
            target_global_id=root.target_global_id,
            uuid=root.id,
            mimetype=root.content_type,
        )
        public_transient_url = Upload.generate_pre_signed_url_for_get(name=path)
        return public_transient_url

    @classmethod
    def resolve_pre_signed_url(cls, root: Upload, info, **kwargs):
        organization = info.context.user.profile.organization()
        path = Upload.generate_path(
            location=Upload.Location(root.location),
            organization=organization,
            target_global_id=root.target_global_id,
            uuid=root.id,
            mimetype=root.content_type,
        )
        public_transient_url = Upload.generate_pre_signed_url_for_put(
            name=path,
            content_type=root.content_type,
        )
        return public_transient_url

    @classmethod
    def resolve_file_url(cls, root: Upload, info, **kwargs):
        # TODO: We are using presingned url always to test if that fixes CORS issue
        # if Upload.Location(root.location) == Upload.Location.PUBLIC:
        #     return root.public_url.split('?')[0]
        user: User = info.context.user
        if user.is_authenticated:  # and Upload.Location(root.location) == Upload.Location.STATIC:
            # Placeholder, proper ACL should go here for static documents
            organization = info.context.user.profile.organization()
            path = Upload.generate_path(
                location=Upload.Location(root.location),
                organization=organization,
                target_global_id=root.target_global_id,
                uuid=root.id,
                mimetype=root.content_type,
            )
            public_transient_url = Upload.generate_pre_signed_url_for_get(name=path)
            return public_transient_url
        return None

    @classmethod
    def resolve_public_permanent_url(cls, root: Upload, info, **kwargs):
        if Upload.Location(root.location) == Upload.Location.PUBLIC:
            return root.public_url.split('?')[0]
        return None


class FileUploadType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    path = graphene.String(source='path', description='Path of the file uploaded.')
    content_type = graphene.String(source='content_type', description='Content type of the file uploaded.')
    public_url = graphene.String(source='public_url', description='Public URL of the file uploaded.')
    pre_signed_url = graphene.String(source='pre_signed_url', description='Pre signed URL of the file uploaded.')
    target_global_id = graphene.String(
        source='target_global_id',
        description='Global ID of the target object.',
        required=True
    )

    class Meta(MetaNode):
        model = FileUpload
        fields = 'upload',
