# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['ComponentTest::test_create_ui_component 1'] = {
    'data': {
        'component': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['ComponentTest::test_should_filter_component_by_slug 1'] = {
    'data': {
        'components': {
            'edges': [
            ]
        }
    }
}

snapshots['ComponentTest::test_should_get_all_components 1'] = {
    'data': {
        'components': {
            'edges': [
            ]
        }
    }
}

snapshots['ComponentTest::test_update_ui_component 1'] = {
    'data': {
        'component': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['ComponentTest::test_update_ui_component_id_does_not_exist 1'] = {
    'data': {
        'component': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 15,
                    'line': 3
                }
            ],
            'message': 'Object id ComponentType:Q29tcG9uZW50VHlwZTo1OQ== not found',
            'path': [
                'component'
            ]
        }
    ]
}

snapshots['ComponentTest::test_update_ui_component_invalid_order_sequence 1'] = {
    'data': {
        'component': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 15,
                    'line': 3
                }
            ],
            'message': "[ErrorDetail(string='sort_order must be a positive numeric sequence from zero.', code='invalid')]",
            'path': [
                'component'
            ]
        }
    ]
}
