from unittest.mock import patch

from celery import Task
from config.celery import debug_task
from core.tests.utils.base_test import BaseTest
from django.test import override_settings


class CompanyPagesTest(BaseTest):

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER='memory://', CELERY_BACKEND='memory://')
    @patch("config.celery._internal_debug_task")
    def test_task_runs_synchronously_when_eager(self, internal_debug_task):
        """Tasks dispatched with .delay() must execute in-process when CELERY_TASK_ALWAYS_EAGER is True."""
        task: Task = debug_task
        task.delay()
        assert internal_debug_task.called
