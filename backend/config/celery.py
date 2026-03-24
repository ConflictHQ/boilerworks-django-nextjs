import logging

from celery import Celery
from django.apps import apps
from django.conf import settings
from django.db.models import Model
from kombu.utils.json import register_type

logger = logging.getLogger(__name__)

app = Celery(
    settings.CELERY_APP_NAME,
    backend=settings.CELERY_BACKEND,
    broker=settings.CELERY_BROKER
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


def _internal_debug_task(self):
    logger.info(f'Request: {self.request!r}')
    return True


@app.task(bind=True)
def debug_task(self):
    return _internal_debug_task(self)


# Allow serialization of django models:
register_type(
    Model,
    "model",
    lambda instance: [instance._meta.label, instance.pk],
    lambda identifier: apps.get_model(identifier[0]).objects.get(pk=identifier[1]),
)
