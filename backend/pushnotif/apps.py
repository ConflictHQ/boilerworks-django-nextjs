"""
Push Notifications AppConfig
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PushNotifConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pushnotif'

    @staticmethod
    def post_migrate(sender, **kwargs):
        from .models import DeliveryMethods, NotificationCategories, PushNotification
        PushNotification.post_migration(sender)
        DeliveryMethods.register(sender)
        NotificationCategories.register(sender)

    def ready(self):
        post_migrate.connect(self.post_migrate, sender=self)
        from config.celery import app
        from pushnotif.models import PushNotification
        PushNotification.register_tasks(app)
