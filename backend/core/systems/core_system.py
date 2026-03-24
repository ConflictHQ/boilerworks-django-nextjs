import logging

from config import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class CoreSystem:

    @classmethod
    def user_system(cls):
        return get_user_model().objects.get(username=settings.API_SYSTEM_USER)

    @classmethod
    def notify(cls, created_by, user, message):
        # TODO implement this
        from core.models import Notification
        Notification.objects.get_or_create(created_by=created_by)
        return None
