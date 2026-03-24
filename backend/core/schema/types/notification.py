from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from django.db.models import Q
from strawberry.types import Info

from core.models import Notification
from core.schema.dataloaders import batch_load_users
from core.schema.types.user import UserType


@strawberry_django.type(Notification)
class NotificationType:
    """A notification sent to or from a user."""

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return (
            queryset
            .filter(Q(user=info.context.user))
            .prefetch_related('related_gids')
        )

    @strawberry_django.field
    async def user(self, info: Info) -> Optional[UserType]:
        loader = info.context.get_loader('load_user_by_id', batch_load_users)
        return await loader.load(self.user_id)

    @strawberry_django.field
    async def created_by(self, info: Info) -> Optional[UserType]:
        loader = info.context.get_loader('load_user_by_id', batch_load_users)
        return await loader.load(self.created_by_id)
