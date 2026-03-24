# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['DeviceTokenTest::test_get_all_delivery_method_templates 1'] = {
    'data': {
        'deliveryMethodTemplates': [
            {
                'alwaysSendNotification': False,
                'deliveryMethod': {
                    'name': 'ANDROID'
                },
                'id': 'RGVsaXZlcnlNZXRob2ROb3RpZmljYXRpb25UZW1wbGF0ZVR5cGU6MQ==',
                'neverSendNotification': False,
                'notificationTemplate': {
                    'displayName': 'Test Message received'
                },
                'userNotificationConfig': {
                    'isEnabled': True
                }
            },
            {
                'alwaysSendNotification': False,
                'deliveryMethod': {
                    'name': 'IOS'
                },
                'id': 'RGVsaXZlcnlNZXRob2ROb3RpZmljYXRpb25UZW1wbGF0ZVR5cGU6Mg==',
                'neverSendNotification': False,
                'notificationTemplate': {
                    'displayName': 'Test Message received'
                },
                'userNotificationConfig': {
                    'isEnabled': True
                }
            }
        ]
    }
}
