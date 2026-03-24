import logging
from datetime import timedelta
from typing import Optional

from core.models.process import DataProcess, DataProcessEntity
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
            hour='1',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

    def run(self):
        logger.info('Starting deletion of data process records older than 30 days')
        try:
            batch = 1000
            thirty_days_ago = timezone.now() - timedelta(days=30)
            to_delete = DataProcessEntity.objects.filter(created_at__lt=thirty_days_ago)[:batch]
            parent_processes_to_delete = set(to_delete.values_list('process_id', flat=True))
            while to_delete.count() > 0:
                DataProcessEntity.objects.filter(id__in=to_delete).delete()
                DataProcess.objects.filter(batch__in=parent_processes_to_delete).delete()
                to_delete = DataProcessEntity.objects.filter(created_at__lt=thirty_days_ago)[:batch]
                parent_processes_to_delete = set(to_delete.values_list('process_id', flat=True))
            logger.info('Finished deletion of data process records older than 30 days')
        except Exception as e:
            logger.exception(e)
        return {
            self.name: "Completed"
        }
