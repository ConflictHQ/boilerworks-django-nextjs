# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['PermissionsTest::test_add_user_to_permission_group 1'] = {
    'data': {
        'permissionGroupOperation': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['PermissionsTest::test_get_permission_group_filter_by_id 1'] = {
    'data': {
        'groups': {
            'edges': [
                {
                    'node': {
                        'id': 'R3JvdXBUeXBlOjQ=',
                        'name': 'TestGroup',
                        'userSet': {
                            'edges': [
                            ]
                        }
                    }
                }
            ]
        }
    }
}

snapshots['PermissionsTest::test_get_permission_group_filter_by_name 1'] = {
    'data': {
        'groups': {
            'edges': [
            ]
        }
    }
}

snapshots['PermissionsTest::test_get_permission_group_with_only_filtered_users_by_search 1'] = {
    'data': {
        'groups': {
            'edges': [
                {
                    'node': {
                        'id': 'R3JvdXBUeXBlOjQ=',
                        'name': 'TestGroup',
                        'userSet': {
                            'edges': [
                            ],
                            'totalCount': 0
                        }
                    }
                }
            ]
        }
    }
}

snapshots['PermissionsTest::test_get_permission_groups 1'] = {
    'data': {
        'groups': {
            'edges': [
                {
                    'node': {
                        'id': 'R3JvdXBUeXBlOjQ=',
                        'name': 'TestGroup'
                    }
                }
            ]
        }
    }
}

snapshots['PermissionsTest::test_remove_user_from_permission_group 1'] = {
    'data': {
        'permissionGroupOperation': {
            'errors': [
            ],
            'ok': True
        }
    }
}
