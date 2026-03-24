from core.models import Tracking
from django.conf import settings
from django.db import models
from pushnotif.models import DeliveryMethod


class DeviceToken(Tracking):
    name = models.CharField(
        max_length=128,
        blank=False,
        null=False
    )

    device_token = models.CharField(
        primary_key=True,
        max_length=1024
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    delivery_method = models.ForeignKey(
        DeliveryMethod,
        on_delete=models.CASCADE,
        null=True
    )
