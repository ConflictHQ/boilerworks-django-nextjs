from core.tests.utils.base_test import BaseTest
from pushnotif.models.delivery_method import DeliveryMethod
from pushnotif.models.notification import DeliveryMethodNotificationTemplate, NotificationTemplate


class DeviceTokenTest(BaseTest):
    def setUp(self):
        super().setUp()
        android, _ = DeliveryMethod.objects.get_or_create(name='ANDROID', defaults={'display_name': 'Android'})
        ios, _ = DeliveryMethod.objects.get_or_create(name='IOS', defaults={'display_name': 'IOS'})
        notif_template, _ = NotificationTemplate.objects.get_or_create(
            name='message/received',
            defaults={
                'display_name': 'Test Message received',
                'app_label': 'core',
                'classname': 'Notifications',
                'member': 'MESSAGE_RECEIVED',
                'parameters': 'TestParameters',
            }
        )
        DeliveryMethodNotificationTemplate.objects.get_or_create(
            notification_template=notif_template,
            delivery_method=android,
            defaults={'always_send_notification': False, 'never_send_notification': False},
        )
        DeliveryMethodNotificationTemplate.objects.get_or_create(
            notification_template=notif_template,
            delivery_method=ios,
            defaults={'always_send_notification': False, 'never_send_notification': False},
        )

    def test_get_all_delivery_method_templates(self):
        """
        # Get all delivery method templates
        Displays the structure and the configuration of each notification message per delivery method
        """

        request = self.request()
        mutation = '''
        query DeliveryMethodTemplates {
          deliveryMethodTemplates {
            userNotificationConfig {
              isEnabled
            }
            deliveryMethod {
              name
            }
            notificationTemplate {
              displayName
            }
            neverSendNotification
            alwaysSendNotification
            id
          }
        }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)
