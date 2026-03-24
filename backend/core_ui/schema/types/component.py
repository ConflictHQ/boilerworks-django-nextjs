import django_filters
import graphene_django_optimizer as gql_optimizer
from core.schema import DjangoObjectTypeUtils, DjangoPermissionFilterMixin, MetaNode
from core_ui.models import Component, ComponentQuerySet
from graphene_django import DjangoObjectType


class ComponentFilter(django_filters.FilterSet):
    slug = django_filters.CharFilter(method='_filter_by_slug')

    class Meta:
        model = Component
        fields = ['slug']

    def _filter_by_slug(self, queryset, name, value):
        qs = queryset.filter(slug=value)
        if qs.exists():
            return qs

        component = Component.objects.filter(slug=value).first()
        if component:
            from core_logs.models import PermissionAccessLog
            PermissionAccessLog.log_denied(
                self.request.user,
                component.permissions.filter(codename__startswith='view_').first(),
                msg=f'User does not have access to component with slug "{value}"')
            return queryset.none()

        raise ValueError(f'Component with slug "{value}" does not exist')


class ComponentType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    class Meta(MetaNode):
        model = Component
        fields = '__all__'
        filterset_class = ComponentFilter

    @classmethod
    def get_queryset(cls, queryset: ComponentQuerySet, info):
        return gql_optimizer.query(queryset.all(), info)
        # return queryset #.with_view_permission_info(info)

    @classmethod
    def resolve_components(cls, root: Component, info, **kwargs):
        qs = root.components.filter(
            pk__in=Component.objects.filter(permissions__group__in=info.context.user.groups.all()))

        slugs = list(root.components.exclude(pk__in=qs).values_list('slug', flat=True))

        if len(slugs):
            from core_logs.models import PermissionAccessLog
            slugs = ', '.join(slugs)
            PermissionAccessLog.log_denied(
                info.context.user,
                msg=f'User does not have access to components: "{slugs}"')

        return qs.order_by('through_parents__order')
        # return root.ordered_components
