from core.models import Profile
from pushnotif.models import DeliveryMethodNotificationTemplate
from pushnotif.models.notification_config import NotificationConfig


class NotificationConfigValidator:
    def __init__(self, profile: Profile):
        self.profile = profile

    def check_notification_config(self, delivery_method_template: DeliveryMethodNotificationTemplate):
        if delivery_method_template.never_send_notification:
            return False

        if delivery_method_template.always_send_notification:
            return True

        notification_config_is_enabled = NotificationConfig.objects.filter(
            profile=self.profile,
            delivery_method_template=delivery_method_template
            ).values_list("is_enabled", flat=True).first()
        if notification_config_is_enabled is not None:
            return notification_config_is_enabled
        else:
            return True
