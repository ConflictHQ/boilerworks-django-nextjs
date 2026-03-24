import django.apps
import django_filters
import graphene
from config.permissions import AbstractPermissions, FieldPermissions
from core.models import Tracking
from core.schema import DjangoObjectTypeUtils, MetaNode, UserType
from core.systems.permission_system import Action, PermissionSystem
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Field
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter
from organization.models import Organization


class FieldPermissionType(graphene.ObjectType):
    name = graphene.String()
    add = graphene.Boolean(default_value=False)
    view = graphene.Boolean(default_value=False)
    change = graphene.Boolean(default_value=False)
    delete = graphene.Boolean(default_value=False)

    @staticmethod
    def resolve_name(root: FieldPermissions, info, **kwargs):
        return root.name

    @staticmethod
    def resolve_add(root: FieldPermissions, info, **kwargs):
        return root.can_add(info.context.user)

    @staticmethod
    def resolve_view(root: FieldPermissions, info, **kwargs):
        return root.can_view(info.context.user)

    @staticmethod
    def resolve_change(root: FieldPermissions, info, **kwargs):
        return root.can_change(info.context.user)

    @staticmethod
    def resolve_delete(root: FieldPermissions, info, **kwargs):
        return root.can_delete(info.context.user)


class FieldType(graphene.ObjectType):
    field_type = graphene.String()
    name = graphene.String()
    verbose_name = graphene.String()
    permissions = graphene.Field(FieldPermissionType)

    @staticmethod
    def resolve_field_type(root: Field, info, **kwargs):
        return root.__class__.__name__

    @staticmethod
    def resolve_name(root: Field, info, **kwargs):
        return root.name

    @staticmethod
    def resolve_verbose_name(root: Field, info, **kwargs):
        return root.verbose_name

    @staticmethod
    def resolve_permissions(root: Field, info, **kwargs):
        return root.permission


class ModelType(graphene.ObjectType):
    model_name = graphene.String()
    verbose_name = graphene.String()
    verbose_name_plural = graphene.String()
    permissions = graphene.List(FieldPermissionType)
    fields = graphene.List(FieldType)

    @staticmethod
    def resolve_model_name(root: Tracking, info, **kwargs):
        return root._meta.model_name

    @staticmethod
    def resolve_verbose_name(root: Tracking, info, **kwargs):
        return root._meta.verbose_name

    @staticmethod
    def resolve_verbose_name_plural(root: Tracking, info, **kwargs):
        return root._meta.verbose_name_plural

    @staticmethod
    def resolve_permissions(root: Tracking, info, **kwargs):
        return root.model_permissions().permissions

    @staticmethod
    def resolve_fields(root: Tracking, info, **kwargs):
        fields = []
        for field in root._meta.fields:
            permission = root.model_permissions().permissions_map.get(field.name)
            if permission and permission.can_view(info.context.user):
                field.permission = permission
                fields.append(field)

        return fields


class GroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', field_name='name')
    id = GlobalIDFilter(method='_filter_by_id')

    class Meta:
        model = Group
        fields = ['id', 'name']

    def _filter_by_id(self, queryset, name, value):
        if value:
            return queryset.filter(id=GroupType.get_pk(value))
        return queryset


class GroupType(DjangoObjectType, DjangoObjectTypeUtils):
    user_set = DjangoFilterConnectionField(UserType)

    class Meta(MetaNode):
        model = Group
        fields = '__all__'
        filterset_class = GroupFilter

    @classmethod
    def get_queryset(cls, queryset, info):
        user: User = info.context.user
        AbstractPermissions.check_django_auth_permission(user, 'group', Action.VIEW, raised_error=True)
        organization: Organization = user.profile.organization()
        return queryset.filter(organizations__exact=organization.id).order_by('name')


class PermissionType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = Permission


class ContentTypeType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = ContentType


class PermissionCategoryType(graphene.ObjectType):
    name = graphene.String()
    categories = graphene.List('core.schema.permissions.PermissionCategoryType')
    permissions = graphene.List(PermissionType)

    @staticmethod
    def resolve_name(root, info, **kwargs):
        return root.name

    @staticmethod
    def resolve_categories(root, info, **kwargs):
        return root.categories.values()

    @staticmethod
    def resolve_permissions(root, info, **kwargs):
        return [a.permission for a in root.actions.values()]


class PermissionsQuery(graphene.ObjectType):
    permission_categories = graphene.Field(PermissionCategoryType)
    groups = DjangoFilterConnectionField(GroupType)
    models = graphene.List(ModelType)
    content_type = graphene.List(ContentTypeType)
    model = graphene.Field(ModelType, name=graphene.String())

    @staticmethod
    def resolve_model(root, info, name, **kwargs):
        content_type = ContentType.objects.get(model__iexact=name)
        return django.apps.apps.get_model(content_type.app_label, name)

    @staticmethod
    def resolve_permission_categories(root, info, **kwargs):
        return PermissionSystem.permissions_categories()

    @staticmethod
    def resolve_models(root, info, **kwargs):
        return [obj for obj in django.apps.apps.get_models() if hasattr(obj, 'model_permissions')]

    @staticmethod
    def resolve_content_type(root, info, **kwargs):
        return ContentType.objects.all()
