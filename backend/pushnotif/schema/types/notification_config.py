from core.schema import DjangoObjectTypeUtils, DjangoPermissionFilterMixin
from django_filters import FilterSet
from graphene_django import DjangoObjectType
from pushnotif.models.notification_config import NotificationConfig


class NotificationConfigFilter(FilterSet):
    class Meta:
        model = NotificationConfig
        fields = "__all__"


class NotificationConfigType(
    DjangoPermissionFilterMixin,
    DjangoObjectTypeUtils,
    DjangoObjectType
):
    class Meta:
        model = NotificationConfig
        fields = ['is_enabled']
        filterset_class = NotificationConfigFilter

    @classmethod
    def get_queryset(cls, queryset, info):
        if not info.context.user.is_authenticated:
            return NotificationConfig.objects.none()
        return queryset.filter(profile=info.context.user.profile)
