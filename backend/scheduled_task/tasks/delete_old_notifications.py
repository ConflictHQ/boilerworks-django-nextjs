import logging
from datetime import timedelta
from typing import Optional

from core.models import Notification
from django.utils import timezone
from django.utils.functional import classproperty
from django_celery_beat.models import CrontabSchedule
from pushnotif.models.notification import EmailNotification, NotificationEvent, NotificationEventMethod, PushNotification, SMSNotification
from scheduled_task.tasks import BaseTask

logger = logging.getLogger(__name__)


class Task(BaseTask):

    @classproperty
    def schedule(cls) -> Optional[CrontabSchedule]:
        return CrontabSchedule(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

    @classmethod
    def run(self):
        logger.info("Deleting notifications older than 30 days")
        batch_size = 1000
        thirty_days_ago = timezone.now() - timedelta(days=30)

        models_to_clean = [
            SMSNotification,
            EmailNotification,
            PushNotification,
            Notification,
            NotificationEventMethod,
            NotificationEvent
        ]

        def delete_old_records(model_class):
            records = model_class.objects.filter(created_at__lt=thirty_days_ago)[:batch_size]
            while records.count() > 0:
                model_class.objects.filter(id__in=records).delete()
                records = model_class.objects.filter(created_at__lt=thirty_days_ago)[:batch_size]

        for model in models_to_clean:
            delete_old_records(model)

        return {
            self.name: "succeeded"
        }
