from typing import Optional, Type

from auth1.models import UserInfo
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet
from django.utils.functional import cached_property

from ..common import Tracking
from .actions import SharedResourcePermission


class SharedResourceNameManager(models.Manager):
    use_in_migrations = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache shared by all the get_for_* methods to speed up
        # ContentType retrieval.
        self._cache = {}

    def get_by_natural_key(self, name):
        result: Optional[SharedResourceName] = self._cache.get(name)
        if result is not None:
            return result
        result = self.filter(name=name).first()
        if result is not None:
            self._cache[name] = result
        return result

    @classmethod
    def get_name_of_resource(cls, resource: "SharedResource"):
        content_type = ContentType.objects.get_for_model(resource.__class__)
        return f"srn://{content_type.app_label}/{content_type.model}/{resource.pk}"

    def get_by_resource(self, resource: "SharedResource", create: bool = False):
        name = self.get_name_of_resource(resource)
        result: Optional[SharedResourceName] = self.get_by_natural_key(name)
        if result is not None:
            return result
        if create:
            content_type = ContentType.objects.get_for_model(resource.__class__)
            global_id: Optional[str] = None
            if hasattr(resource, "global_id"):
                match resource.global_id:
                    case str():
                        global_id = resource.global_id
                    case _ if hasattr(resource.global_id, '__call__'):
                        global_id = resource.global_id()
            result = self.create(
                name=name,
                content_type=content_type,
                content_object=resource,
                object_id=resource.pk,
                global_id=global_id,
            )
            self._cache[name] = result
        return result


class SharedResourceName(models.Model):
    objects = SharedResourceNameManager()

    name = models.CharField(max_length=1024, primary_key=True)
    object_id = models.PositiveIntegerField(null=False)
    global_id = models.CharField(max_length=1024, null=True, unique=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=False)
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.name


class SourceSharedResourcePolicy(models.Model):
    resource = models.ForeignKey(
        SharedResourceName,
        on_delete=models.CASCADE,
        related_name="+",
    )

    policy = models.ForeignKey(
        "SharedResourcePolicy",
        on_delete=models.CASCADE,
    )


class TargetSharedResourcePolicy(models.Model):
    resource = models.ForeignKey(
        SharedResourceName,
        on_delete=models.CASCADE,
        related_name="+",
    )

    policy = models.ForeignKey(
        "SharedResourcePolicy",
        on_delete=models.CASCADE
    )


class PermissionSharedResourcePolicy(models.Model):
    permission = models.ForeignKey(
        SharedResourcePermission,
        on_delete=models.CASCADE,
    )

    policy = models.ForeignKey(
        "SharedResourcePolicy",
        on_delete=models.CASCADE
    )


class SharedResourcePolicy(Tracking):
    name = models.CharField(max_length=1024)

    source_resources = models.ManyToManyField(
        SharedResourceName,
        through=SourceSharedResourcePolicy,
        related_name="+",
    )

    target_resources = models.ManyToManyField(
        SharedResourceName,
        through=TargetSharedResourcePolicy,
        related_name="+",
    )

    permissions = models.ManyToManyField(
        SharedResourcePermission,
        through=PermissionSharedResourcePolicy,
        related_name="+",
    )

    def __str__(self):
        return self.name


_shared_resource_models: [Type["SharedResource"]] = set()


class Principal(UserInfo):
    class Meta:
        proxy = True

    def source_resources(self) -> QuerySet[SharedResourceName]:
        resources = SharedResourceName.objects.none()
        shared_resource_model: Type[SharedResource]
        for shared_resource_model in _shared_resource_models:
            resources |= shared_resource_model.from_principal(self)
        resources = resources.distinct()
        return resources


class SharedResource(models.Model):
    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        _shared_resource_models.add(cls)

    @classmethod
    def from_principal(cls, principal: Principal) -> QuerySet[SharedResourceName]:
        return SharedResourceName.objects.none()

    @cached_property
    def shared_resource_name(self) -> SharedResourceName:
        return SharedResourceName.objects.get_by_resource(self, create=True)


__all__ = [
    'SharedResource',
    'SharedResourcePolicy',
    'SourceSharedResourcePolicy',
    'TargetSharedResourcePolicy',
    'SharedResourcePermission',
    'Principal',
]
