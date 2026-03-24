import enum
import logging

from core.models import Tracking
from django.apps import AppConfig
from django.db import DatabaseError, models
from django.utils.functional import cached_property

from .delivery_method import DeliveryMethod, DeliveryMethods

logger = logging.getLogger(__name__)


class NotificationCategory(Tracking):
    name = models.CharField(max_length=64, primary_key=True)

    delivery_methods = models.ManyToManyField(DeliveryMethod)

    android = models.JSONField(null=True, blank=True, default=dict)

    ios = models.JSONField(null=True, blank=True, default=dict)

    webapp = models.JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return f'{self.name}'


class NotificationCategories(enum.Enum):
    TODO = {
        'name': 'TODO',
        'delivery_methods': {
            DeliveryMethods.IOS,
            DeliveryMethods.ANDROID,
            DeliveryMethods.WEBAPP,
        },
    }

    NOTICES = {
        'name': 'Notices',
        'delivery_methods': {
            DeliveryMethods.IOS,
            DeliveryMethods.ANDROID,
            DeliveryMethods.WEBAPP,
            DeliveryMethods.SMS,
        },
    }

    REMINDERS = {
        'name': 'Reminders',
        'delivery_methods': {
            DeliveryMethods.IOS,
            DeliveryMethods.ANDROID,
            DeliveryMethods.WEBAPP,
        },
    }

    def __new__(cls, data, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = data['name']
        return obj

    def __init__(self, data):
        self.delivery_methods = frozenset(data['delivery_methods'])

    def __str__(self):
        return self.name

    @cached_property
    def model(self):
        model, created = NotificationCategory.objects.get_or_create(name=str(self))
        for delivery_method in self.delivery_methods:
            model.delivery_methods.add(delivery_method.model)
        return model

    @classmethod
    def default_notification_category(cls):
        return cls.NOTICES.model

    @classmethod
    def register(cls, app_config: AppConfig):
        try:
            NotificationCategory.objects.count()
        except DatabaseError:
            logger.error(f'Unable to access {cls} model')
            return
        for member in cls:
            model = member.model
            logger.debug(f'Registering {cls.__name__}.{model}')


__all__ = [
    'DeliveryMethod',
    'DeliveryMethods',
    'NotificationCategory',
    'NotificationCategories',
]
