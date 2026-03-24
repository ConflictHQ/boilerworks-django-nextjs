import uuid
from datetime import datetime, timedelta
from enum import Enum

import pytz
from core.utils import cached_classproperty
from core.utils.performance import cache_class_method
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from graphene_django.registry import get_global_registry
from graphql_relay import from_global_id
from simple_history.models import HistoricalRecords


class QueryOperator(Enum):
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    EXACT = "exact"


class ModelPermissionsMixin:

    @classmethod
    @cache_class_method(timeout=timedelta(minutes=1))
    def model_permissions(cls):
        from config.permissions import ModelPermissions
        return ModelPermissions(model=cls)

    @classmethod
    def p(cls, element: str):
        return cls.model_permissions()[element]

    @classmethod
    def get_queryset(cls, queryset: QuerySet, user: settings.AUTH_USER_MODEL) -> QuerySet:
        """
        Filter queryset by user permissions
        """
        # Superusers bypass all permission checks
        if user and user.is_authenticated and user.is_superuser:
            return queryset

        if cls.p('model').view:
            cls.p('model').view.check(user)
        else:
            from core_logs.models import PermissionAccessLog
            PermissionAccessLog.log_denied(user,
                                           msg=f'Indirect error. Model {cls.p("model")} has no view permission. '
                                               f'This also happens if permissions object P has not been updated.')
            raise PermissionError(f'User {user} has no view permission for {cls.p("model")}')

        return queryset

    @classmethod
    def can_add(cls, user: settings.AUTH_USER_MODEL):
        cls.p('model').add and cls.p('model').add.check(user)

    @classmethod
    def can_change(cls, user: settings.AUTH_USER_MODEL):
        cls.p('model').change and cls.p('model').change.check(user)

    @property
    def global_id(self):
        from graphene_django.registry import get_global_registry

        registry = get_global_registry()
        return registry.get_type_for_model(type(self)).to_global_id(self)

    def delete_check(self, info, *args, **kwargs):
        """
        Check if user has permission to delete the object and delete it if so.
        """
        self.model_permissions()['model'].delete.check(info.context.user)
        self.delete(*args, **kwargs)


class Tracking(ModelPermissionsMixin, models.Model):
    class Meta:
        abstract = True

    version = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   verbose_name='Creator',
                                   related_name='created_%(class)s',
                                   null=True,
                                   blank=True,
                                   on_delete=models.SET_NULL)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   related_name='modified_%(class)s',
                                   null=True,
                                   blank=True,
                                   on_delete=models.SET_NULL)

    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   related_name='deleted_%(class)s',
                                   null=True,
                                   blank=True,
                                   on_delete=models.SET_NULL)

    history = HistoricalRecords(inherit=True)

    def save(self, *args, **kwargs):
        self.version = self.version + 1
        super().save(*args, **kwargs)

    @cached_classproperty
    def local_timezone(cls) -> timezone:
        return pytz.timezone(settings.COMPANY_TIME_ZONE)

    @cached_property
    def localized_created_at(self) -> datetime:
        return self.created_at.astimezone(self.local_timezone)

    @property
    def global_id(self):
        from graphene_django.registry import get_global_registry

        registry = get_global_registry()
        return registry.get_type_for_model(type(self)).to_global_id(self)


class ResourceFile(Tracking):
    gid = models.UUIDField(primary_key=True, help_text='Unique resource file id')

    name = models.CharField(max_length=250, help_text='User friendly name')
    is_public = models.BooleanField(default=False)
    file = models.FileField(upload_to=settings.GS_DIR, null=True, blank=True)

    @property
    def url(self):
        from core.systems import StorageSystem
        return StorageSystem.get_url(self)


class GlobalIDMap(models.Model):
    obj_guid = models.CharField(max_length=100, editable=False, unique=True, db_index=True)
    content_type = models.ForeignKey('contenttypes.ContentType',
                                     related_name='global_id_maps',
                                     on_delete=models.CASCADE)


class BaseCoreModelQuerySet(models.QuerySet):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class BaseCoreModel(Tracking):
    objects = BaseCoreModelQuerySet.as_manager()

    guid = models.UUIDField(editable=False, default=uuid.uuid4)

    name = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(max_length=100, null=True, blank=True, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name

        if not self.name:
            self.name = self.slug

        self.slug = slugify(self.slug)
        super().save(*args, **kwargs)

    def natural_key(self):
        return self.slug,

    def global_id(self):
        registry = get_global_registry()
        return registry.get_type_for_model(type(self)).to_global_id(self)

    @classmethod
    def validate_data(cls, data: [dict, models.Model]):
        return data


class CoreGQLMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        save_global_id = not self.pk
        super().save(*args, **kwargs)

        if save_global_id:
            content_type = ContentType.objects.get_for_model(self)
            GlobalIDMap.objects.create(obj_guid=self.guid, content_type=content_type)

    @classmethod
    def get_obj(cls, info, global_id):
        obj_map = GlobalIDMap.objects.get(obj_guid=global_id)
        model_class = obj_map.content_type.model_class()
        return model_class.objects.get(guid=obj_map.obj_guid)


def validate_gid(value):
    model, pk = from_global_id(value)
    if pk is None:
        raise ValidationError(
            'Invalid global id',
            params={'value': value},
        )


class GlobalIDLinkQuerySet(models.QuerySet):

    def get_or_create_link(self, instance, name=None, description=None, type=None):
        return self.get_or_create(
            app_label=instance._meta.app_label,
            gid=instance.global_id,
            defaults=dict(
                name=name or str(instance),
                type=type or instance.__class__.__name__,
                description=description,
            )
        )


class GlobalIDLink(models.Model):
    """
    A model to store global id links between models. This is useful to store
    generic relations for other apps.
    """
    objects = GlobalIDLinkQuerySet.as_manager()

    app_label = models.CharField(max_length=100)
    gid = models.CharField(max_length=100, db_index=True, validators=[validate_gid], unique=True)
    name = models.CharField(max_length=256, db_index=True)
    type = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.app_label:
            model_name, pk = from_global_id(self.gid)
            if model_name.endswith('Type'):
                try:
                    model = apps.get_model(self.app_label, model_name.replace('Type', ''))
                    obj = model.objects.get(pk=pk)
                    return f'{obj}:{self.gid}'
                except Exception as e:
                    print(f'Model {model_name} with pk {pk} error. {e}')
        return f'{self.name}:{self.gid}'

    def get_instance(self):
        model_name, pk = from_global_id(self.gid)
        if not pk:
            return None
        model_name = model_name if model_name != 'FormSubmissionType' else 'DailyReviewFormSubmission'
        model = apps.get_model(self.app_label, model_name.replace('Type', ''))
        return model.objects.filter(pk=pk).first()

    @property
    def type_name(self):
        type_name, pk = from_global_id(self.gid)
        return type_name


class Link(Tracking):
    url = models.URLField()  # Ensure URLs are unique

    title = models.CharField(blank=True, null=True, max_length=255)  # Optional: a descriptive title for the link
    description = models.TextField(blank=True, null=True)  # Optional: a description of the link

    def __str__(self):
        return self.title or self.url


class MetaclassAbcTracking(models.Model):
    """Abstract base model for models that declare abstract methods for subclasses to implement."""

    class Meta:
        abstract = True


class RequiresApproveMixin:

    def promote(self) -> None:
        raise NotImplementedError()

    def reject(self) -> None:
        raise NotImplementedError()
