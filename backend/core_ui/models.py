from core.models import BaseCoreModel, CoreGQLMixin
from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import signals
from django.db.transaction import on_commit
from django.dispatch import receiver


class ComponentQuerySet(models.QuerySet):

    def with_view_permission(self, user: AUTH_USER_MODEL):
        # TODO change this to use FieldPermission
        user_groups = user.groups.filter(memberships__organization=user.profile.organization())
        user_permissions = Permission.objects.filter(group__in=user_groups)
        return self.filter(permissions__codename__startswith='view_', permissions__in=user_permissions)

    def with_view_permission_info(self, info):
        return self.with_view_permission(info.context.user)

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Component(CoreGQLMixin, BaseCoreModel):
    objects = ComponentQuerySet.as_manager()

    is_active = models.BooleanField(default=True)

    path = models.CharField(max_length=100, null=True, blank=True,
                            help_text='Path to the component')

    icon = models.CharField(max_length=100, null=True, blank=True)

    properties = models.JSONField(default=dict, blank=True, null=True,
                                  help_text='Component properties in JSON format')

    components = models.ManyToManyField('self', blank=True, symmetrical=False,
                                        through='ComponentRelationship',
                                        related_name='parents',
                                        help_text='Components that are children of this component')

    permissions = models.ManyToManyField(Permission, blank=True, related_name='components',
                                         help_text='Permissions that are required to access this component')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def ordered_components(self):
        return self.components.order_by('through_parents__order')

    @staticmethod
    @receiver(signals.post_save, sender='core_ui.Component')
    def add_permissions(sender, instance, created, **kwargs):
        on_commit(instance.syn_permissions)

    def syn_permissions(self):
        content_type = ContentType.objects.get_for_model(self)
        prefixes = ('view', 'add', 'change', 'delete')

        for prefix in prefixes:
            codename = f'{prefix}_{self.slug}'
            permission, created = Permission.objects.get_or_create(
                content_type=content_type,
                codename=codename,
                name=f'Can {prefix} "{self.slug}"'
            )
            self.permissions.add(permission)


class ComponentRelationshipQuerySet(models.QuerySet):

    def get_by_natural_key(self, parent, child):
        parent = Component.objects.get_by_natural_key(parent)
        child = Component.objects.get_by_natural_key(child)

        return self.get(parent=parent, child=child)


class ComponentRelationship(models.Model):
    objects = ComponentRelationshipQuerySet.as_manager()

    parent = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='through_children')  # TODO set on_delete to set null
    child = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='through_parents')
    order = models.PositiveIntegerField()  # This field will determine the order

    class Meta:
        ordering = ['order']

    def natural_key(self):
        return self.parent.natural_key() + self.child.natural_key()

    natural_key.dependencies = ['core_ui.component', 'core_ui.component']
