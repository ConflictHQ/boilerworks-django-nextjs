import logging
from typing import Optional

import celery
import pydash
from celery import current_app
from django.apps.config import AppConfig
from django.utils.functional import classproperty
from django_celery_beat.models import CrontabSchedule, PeriodicTask

logger = logging.getLogger(__name__)


class BaseTask(celery.Task):
    """
    Base class for all scheduled_task.
    """

    TASK_CLASS_NAME = "Task"

    _tasks: dict[str, type] = {}

    def __new__(cls, *args, **kwargs):
        attr = '_instance'
        if not hasattr(cls, attr):
            instance = object.__new__(cls)
            setattr(cls, attr, instance)
        return getattr(cls, attr)

    def __init_subclass__(cls, **kwargs):
        assert cls.__name__ == cls.TASK_CLASS_NAME
        cls._tasks[cls.__module__] = cls

    def __call__(self, *args, **kwargs) -> None:
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @classproperty
    def schedule(cls) -> Optional[CrontabSchedule]:
        return None

    @classproperty
    def name(cls) -> str:
        return pydash.human_case(cls.__module__.split('.')[-1])

    @staticmethod
    def _fix_periodic_task_admin(sender, **kwargs):
        try:
            from config.celery import app
            from django_celery_beat.admin import PeriodicTaskAdmin
            PeriodicTaskAdmin.celery_app = app
            logging.info('PeriodicTaskAdmin.celery_app fixed')
        except Exception as e:
            logging.exception(f'Exception while _fix_periodic_task_admin: {e}')

    @classmethod
    def register_on_celery(cls):
        cls._fix_periodic_task_admin(cls)
        for clazz in cls._tasks.values():
            task = current_app.register_task(clazz)
            logger.info(f'Registering task: {task}')

    @classmethod
    def post_migration(cls, app_config: AppConfig):
        for clazz in cls._tasks.values():
            schedule: Optional[CrontabSchedule] = clazz.schedule
            task_name: str = clazz.name
            if schedule is not None:
                hash_id = abs(hash(clazz.__module__)) % (1 << 16)
                queryset = PeriodicTask.objects.filter(name=task_name)
                if queryset.exists():
                    queryset.update(task=task_name)
                else:
                    schedule.id = hash_id
                    schedule.save()
                    PeriodicTask.objects.create(
                        id=hash_id,
                        name=task_name,
                        task=task_name,
                        crontab=schedule,
                        enabled=False,
                    )
            logger.info(f"Registered {task_name}")
