import abc

from core.models import MetaclassAbcTracking
from django.contrib.auth.models import User
from django.db import models
from pushnotif.models.notification import NotificationTemplate


class BroadcastConfig(MetaclassAbcTracking):
    # The Broadcast configuration must be extended to fulfill
    # the needs of the company domain (i.e. broadcast to managers, or parents or third parties)
    notification_template = models.OneToOneField(
        NotificationTemplate,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    to_users = models.ManyToManyField(User, blank=True)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    @abc.abstractmethod
    def recipients(self) -> [User]:
        ...
