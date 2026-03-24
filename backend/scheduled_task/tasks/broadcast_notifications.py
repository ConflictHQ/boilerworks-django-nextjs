import logging

from django.contrib.auth.models import User
from django.db.models import Model
from pushnotif.models.notification_broadcast import BroadcastConfig
from pushnotif.notification_templates import Notifications
from pushnotif.service import NotificationParameters
from scheduled_task.tasks import BaseTask

logger = logging.getLogger(__name__)


class Task(BaseTask):

    def run(
            self,
            broadcast_config: BroadcastConfig,
            instance: Model,
            notification_type: str,
            original_sender: User,
            original_recipient: User,
            parameters: NotificationParameters,
            *args,
            **kwargs
    ):
        for user in broadcast_config.recipients():
            if user.username == original_sender.username or user.username == original_recipient.username:
                continue

            Notifications[notification_type].send(
                sender=original_sender,
                recipient=user,
                parameters=parameters,
                instance=instance
            )
        return {
            self.name: "succeeded"
        }
