"""Notification mutations migrated from Graphene to Strawberry."""
from __future__ import annotations

import logging

import strawberry
from django.utils import timezone
from graphql import GraphQLError
from strawberry.types import Info

from core.strawberry_schema.common import GlobalIDUtils, MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class NotificationMutations:

    @strawberry.mutation(description="Create or update a notification via NotificationSerializer.")
    def notification(self, info: Info, input: strawberry.scalars.JSON) -> MutationResult:
        from core.serializers.notification import NotificationSerializer

        kwargs = {
            'data': input,
            'partial': True,
            'context': {'request': info.context.request},
        }

        # Handle lookup by guid for updates
        guid = input.get('guid')
        if guid:
            from core.models import Notification
            instance = Notification.objects.filter(guid=guid).first()
            if instance:
                kwargs['instance'] = instance

        serializer = NotificationSerializer(**kwargs)
        if serializer.is_valid():
            serializer.save()
            return MutationResult.success()
        else:
            return MutationResult.from_serializer_errors(serializer.errors)

    @strawberry.mutation(description="Mark a notification as read.")
    def notification_read(self, info: Info, gid: strawberry.ID) -> bool:
        from core.models import Notification, NotificationStatus
        from core.schema import NotificationType

        notification = NotificationType.get_object(info, gid, raise_not_found=True)
        if notification.user != info.context.user:
            raise ValueError('Notification does not belong to user')

        notification.status = NotificationStatus.READ
        notification.status_date = timezone.now()
        notification.save()

        return True
