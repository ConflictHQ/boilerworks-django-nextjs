import enum
import logging

from django.apps import AppConfig
from django.db import DatabaseError, models
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)


class DeliveryMethod(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    display_name = models.CharField(max_length=64)

    @property
    def enum(self) -> "DeliveryMethods":
        return DeliveryMethods[self.name]

    def __str__(self):
        return self.display_name


class DeliveryMethods(enum.Enum):
    ANDROID = 'Android'
    IOS = 'IOS'
    SMS = 'SMS'
    EMAIL = 'Email'
    WEBAPP = 'Web Application'

    @cached_property
    def model(self) -> DeliveryMethod:
        model, _created = DeliveryMethod.objects.get_or_create(name=self.name)
        model.display_name = self.value
        model.save()
        return model

    @classmethod
    def register(cls, app_config: AppConfig):
        try:
            DeliveryMethod.objects.count()
        except DatabaseError:
            logger.error(f'Unable to access {cls} model')
            return
        for delivery_method in cls:
            DeliveryMethod.objects.get_or_create(
                name=delivery_method.name, display_name=delivery_method.value
            )
