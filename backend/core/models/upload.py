import enum
import hashlib
import mimetypes
import uuid
from datetime import datetime, timedelta

from constance import config
from core.models import Tracking
from django.conf.global_settings import AUTH_USER_MODEL
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.encoding import filepath_to_uri
from django.utils.http import urlencode
from organization.models import Organization
from storages.utils import clean_name


class UploadQuerySet(models.QuerySet):

    def with_view_permission(self, user: AUTH_USER_MODEL):
        # TODO change this to use FieldPermission
        # user_groups = user.groups.filter(memberships__organization=user.profile.organization())
        # user_permissions = Permission.objects.filter(group__in=user_groups)
        # return self.filter(permissions__codename__startswith=f'view_', permissions__in=user_permissions)
        return self

    def with_view_permission_info(self, info):
        return self.with_view_permission(info.context.user)

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Upload(Tracking):

    objects = UploadQuerySet.as_manager()

    class Location(enum.Enum):
        """
        Enumeration of locations for uploads
        """

        STATIC = 'static'
        PUBLIC = 'public'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text='Name of the file.'
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text='Description of the file.'
    )

    public_url = models.CharField(
        max_length=4096,
        unique=True,
        null=False,
        blank=False,
    )

    pre_signed_url = models.CharField(
        max_length=4096,
        null=False,
        blank=False,
    )

    path = models.CharField(
        max_length=512,
        unique=True,
        null=True,
        blank=True,
    )

    content_type = models.CharField(
        max_length=256,
        null=False,
        blank=False,
        help_text='Content type of the file. Also known as MIME type.',
    )

    target_global_id = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        db_index=True,
        help_text='Entity the upload belongs to (i.e. a review, a course, an employee...)'
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )

    organization = models.ForeignKey(
        'organization.Organization',
        null=True,
        on_delete=models.CASCADE,
        related_name='uploads'
    )

    location = models.CharField(
        max_length=32,
        choices=[(location.name, location.value) for location in Location],
        default=Location.STATIC.value
    )

    def __str__(self):
        name = self.name[:50] + "..." if self.name and len(self.name) > 50 else self.name
        metadata_name = (self.metadata or {}).get('file_name', None)
        metadata_name = metadata_name[:50] + '...' if metadata_name and len(metadata_name) > 50 else metadata_name
        return f'{name or metadata_name or ""} ({self.id})'

    @classmethod
    def media_storage(cls):
        if not hasattr(cls, '_media_store'):
            cls._media_store = default_storage
        return cls._media_store

    @classmethod
    def generate_path(
            cls,
            location: Location,
            organization: Organization,
            target_global_id: str,
            uuid: uuid.UUID,
            mimetype: str,
    ) -> str:
        pk_hash = hashlib.sha256(str(target_global_id).encode()).hexdigest()
        org_hash = hashlib.sha256(str(organization.global_id).encode()).hexdigest()
        extension = mimetypes.guess_extension(mimetype, strict=False)
        path = f'{location.value}/{org_hash}/{pk_hash}/{uuid.hex}{extension}'
        return path

    @classmethod
    def generate_pre_signed_url_for_get(cls, name, parameters=None, expire=None, content_type=None):
        # Preserve the trailing slash after normalizing the path.
        name = cls.media_storage()._normalize_name(clean_name(name))
        params = parameters.copy() if parameters else {}
        if expire is None:
            expire = config.GET_PRESIGNED_URL_EXPIRATION

        if cls.media_storage().custom_domain:
            url = "{}//{}/{}{}".format(
                cls.media_storage().url_protocol,
                cls.media_storage().custom_domain,
                filepath_to_uri(name),
                "?{}".format(urlencode(params)) if params else "",
            )

            if cls.media_storage().querystring_auth and cls.media_storage().cloudfront_signer:
                print(f'Seconds until expiration {expire}')
                expiration = datetime.utcnow() + timedelta(seconds=expire)
                return cls.media_storage().cloudfront_signer.generate_presigned_url(
                    url, date_less_than=expiration
                )

            # return url

        params["Bucket"] = cls.media_storage().bucket.name
        params["Key"] = name
        custom_url = url
        url = cls.media_storage().bucket.meta.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expire,
        )
        if custom_url:
            query_params = url.split('?')[1]
            url = f'{custom_url}?{query_params}'
        if cls.media_storage().querystring_auth:
            return url
        return cls.media_storage()._strip_signing_parameters(url)

    @classmethod
    def generate_pre_signed_url_for_put(cls, name, parameters=None, expire=None, content_type=None):
        # Preserve the trailing slash after normalizing the path.
        name = cls.media_storage()._normalize_name(clean_name(name))
        params = parameters.copy() if parameters else {}
        if expire is None:
            expire = config.PUT_PRESIGNED_URL_EXPIRATION

        if cls.media_storage().custom_domain:
            url = "{}//{}/{}{}".format(
                cls.media_storage().url_protocol,
                cls.media_storage().custom_domain,
                filepath_to_uri(name),
                "?{}".format(urlencode(params)) if params else "",
            )

            if cls.media_storage().querystring_auth and cls.media_storage().cloudfront_signer:
                expiration = datetime.utcnow() + timedelta(seconds=expire)
                return cls.media_storage().cloudfront_signer.generate_presigned_url(
                    url, date_less_than=expiration
                )

            # return url

        params["Bucket"] = cls.media_storage().bucket.name
        params["Key"] = name
        params["ContentType"] = content_type
        custom_url = url
        url = cls.media_storage().bucket.meta.client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expire,
        )
        if custom_url:
            query_params = url.split('?')[1]
            url = f'{custom_url}?{query_params}'
        if cls.media_storage().querystring_auth:
            return url
        return cls.media_storage()._strip_signing_parameters(url)

    def get_as_object(self):
        return self.media_storage().bucket.meta.client.get_object(Bucket=self.media_storage().bucket.name, Key=self.path)

    def delete_s3_object(self):
        return self.media_storage().bucket.meta.client.delete_object(Bucket=self.media_storage().bucket.name, Key=self.path)

    def delete(self, *args, **kwargs):
        self.delete_s3_object()
        super().delete(*args, **kwargs)


class FileUpload(Tracking):
    upload = models.ForeignKey(
        Upload,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='file_uploads',
    )

    # NOTE: do not define an `id` property here. Django installs the auto pk
    # descriptor on the class *after* the class body executes (Field.contribute_to_class),
    # so a class-body `id` property is silently overwritten and never called.
    # Use `global_id` (from Tracking) for the relay id.

    @property
    def path(self):
        if self.upload:
            return self.upload.path

    @property
    def content_type(self):
        if self.upload:
            return self.upload.content_type

    @property
    def pre_signed_url(self):
        if self.upload:
            return self.upload.pre_signed_url

    @property
    def target_global_id(self):
        if self.upload:
            return self.upload.target_global_id

    @staticmethod
    @receiver(signals.post_save, sender=Upload)
    def on_upload_save(sender, instance, created, **kwargs):
        if created:
            FileUpload.objects.get_or_create(upload=instance)
