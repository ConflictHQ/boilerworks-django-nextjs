import logging

import django_filters
import graphene
from constance import config
from core.models import Notification
from core.schema import DjangoObjectTypeUtils, GlobalIDLinkType, MetaNode
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

logger = logging.getLogger(__name__)

# Optional import - domain search functionality
try:
    from domain_search.documents import NotificationDocument
    HAS_DOMAIN_SEARCH = True
except ImportError:
    NotificationDocument = None
    HAS_DOMAIN_SEARCH = False


class NotificationTypeEnum(graphene.Enum):
    SENT = 'sent'
    RECEIVED = 'received'
    BOTH = 'both'


class NotificationFilter(django_filters.FilterSet):
    notification_type = django_filters.ChoiceFilter(choices=[
        ('SENT', 'Sent'),
        ('RECEIVED', 'Received'),
    ], method='_filter_notification_type')

    search = django_filters.CharFilter(method='_filter_by_search')

    class Meta:
        model = Notification
        fields = dict(
            status=['exact'],
        )

    def _filter_notification_type(self, queryset, name, value):
        user = self.request.user
        if value == 'SENT':
            return queryset.filter(created_by=user)
        elif value == 'RECEIVED':
            return queryset.filter(user=user)
        return queryset

    def _filter_by_search(self, queryset, name, value):
        if not value:
            return queryset

        if config.SEARCH_PROFILE_ENABLED and HAS_DOMAIN_SEARCH:
            logger.info("Using OpenSearch for notification search")

            dp_query_search = {
                "query_string": {
                    "query": f"*{value}*",
                    "fields": ["*"]
                }
            }

            notification_search = NotificationDocument.search().query(dp_query_search)

            ids = [hit.id for hit in notification_search if hit.id is not None]

            logger.info("Found %s notifications via OpenSearch", len(ids))

            return queryset.filter(id__in=ids)
        else:
            logger.info("Using normal database search for notifications")
            result = queryset.lookup(search__icontains=value)
            return result


class NotificationType(DjangoObjectType, DjangoObjectTypeUtils):
    """
    A notification is a message that can be sent to a user.
    Filter by notification_type = ["SENT" | "RECEIVED"]
    """
    related_gids = graphene.List(GlobalIDLinkType, description='Related Global IDs')

    class Meta(MetaNode):
        model = Notification
        filterset_class = NotificationFilter

    @classmethod
    def get_queryset(cls, queryset, info):
        return (
            queryset
            .filter(Q(user=info.context.user))
            .prefetch_related('related_gids')
        )

    @classmethod
    def resolve_related_gids(cls, notification: Notification, info):
        return notification.related_gids.all()

    @classmethod
    def resolve_user(cls, notification: Notification, info):
        return info.context.load_user_by_id(notification.user_id)

    @classmethod
    def resolve_created_by(cls, notification: Notification, info):
        return info.context.load_user_by_id(notification.created_by_id)


class NotificationQuery(graphene.ObjectType):
    notifications = DjangoFilterConnectionField(NotificationType)
