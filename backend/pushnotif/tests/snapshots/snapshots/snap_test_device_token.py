# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['DeviceTokenTest::test_delete_device_token 1'] = {
    'data': {
        'deviceToken': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['DeviceTokenTest::test_get_all_device_tokens_for_current_user 1'] = {
    'data': {
        'devices': [
        ]
    }
}

snapshots['DeviceTokenTest::test_upsert_existing_device_token 1'] = {
    'data': {
        'deviceToken': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['DeviceTokenTest::test_upsert_new_device_token 1'] = {
    'data': {
        'deviceToken': {
            'errors': [
            ],
            'ok': True
        }
    }
}
