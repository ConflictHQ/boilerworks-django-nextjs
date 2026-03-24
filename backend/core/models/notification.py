from core.models import Tracking
from django.conf import settings
from django.db import models


class NotificationStatus(models.TextChoices):
    UNREAD = 'UNREAD', 'Unread'
    READ = 'READ', 'Read'
    DELETE = 'DELETE', 'Delete'
    CANCEL = 'CANCEL', 'Cancel'


class Notification(Tracking):
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=('user', 'status'))]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User to notify',
    )

    subject = models.CharField(max_length=200)
    message = models.TextField(max_length=2000)

    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.UNREAD
    )

    status_date = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, related_name='created_notifications',
        help_text='User who created the notification',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    search = models.TextField(
        null=True,
        blank=True,
        editable=False,
        help_text='Search field for messages',
    )

    related_gids = models.ManyToManyField(
        'core.GlobalIDLink',
        blank=True,
        related_name='notifications',
        help_text='Related Global IDs',
    )

    def save(self, *args, **kwargs):
        self.search = f'{self.subject} {self.message}'
        super().save(*args, **kwargs)
