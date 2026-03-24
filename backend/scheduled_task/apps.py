import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


class ScheduledTaskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduled_task'

    @classmethod
    def post_migrate(cls, sender, **kwargs):
        from scheduled_task.tasks import BaseTask
        BaseTask.post_migration(sender)

    def ready(self):
        post_migrate.connect(self.post_migrate, sender=self)
        from scheduled_task.tasks import BaseTask
        BaseTask.register_on_celery()
