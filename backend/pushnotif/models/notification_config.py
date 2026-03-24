from core.models import Tracking
from django.db import models
from pushnotif.models.notification import DeliveryMethodNotificationTemplate


class NotificationConfig(Tracking):
    """
    Intermediary model that links a user's profile to DeliveryMethodNotificationTemplate.
    This allows users to configure their notification preferences for different notification types.
    """
    profile = models.ForeignKey(
        'core.Profile',
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )

    delivery_method_template = models.ForeignKey(
        DeliveryMethodNotificationTemplate,
        on_delete=models.CASCADE,
        related_name='user_preferences',
    )

    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether the user has enabled notifications for this template and delivery method',
    )

    class Meta:
        unique_together = ('profile', 'delivery_method_template')
        verbose_name = 'User Notification Preference'
        verbose_name_plural = 'User Notification Preferences'
