import logging
from datetime import timedelta
from typing import Optional

from core_logs.models import GQLLog
from django.utils import timezone
from django.utils.functional import classproperty
from django_celery_beat.models import CrontabSchedule
from scheduled_task.tasks import BaseTask

logger = logging.getLogger(__name__)


class Task(BaseTask):

    @classproperty
    def schedule(cls) -> Optional[CrontabSchedule]:
        return CrontabSchedule(
            minute='0',
            hour='23',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

    def run(self):
        logger.info('Starting deletion of gql logs older than 30 days')
        try:
            batch = 1000
            thirty_days_ago = timezone.now() - timedelta(days=30)
            to_delete = GQLLog.objects.filter(created_at__lt=thirty_days_ago)[:batch]
            while to_delete.count() > 0:
                GQLLog.objects.filter(id__in=to_delete).delete()
                to_delete = GQLLog.objects.filter(created_at__lt=thirty_days_ago)[:batch]
            logger.info('Finished deletion of gql logs older than 30 days')
        except Exception as e:
            logger.exception(e)
        return {
            self.name: "Completed"
        }
