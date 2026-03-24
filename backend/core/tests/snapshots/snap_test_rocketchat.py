# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestRocketchat::test_generate_rocket_chat_token 1'] = {
    'data': {
        'generateRocketChatToken': {
            'token': 'abc'
        }
    }
}

snapshots['TestRocketchat::test_generate_rocket_chat_token_exception 1'] = {
    'data': {
        'generateRocketChatToken': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 11,
                    'line': 3
                }
            ],
            'message': 'Failed to generate Rocketchat token for user: testuser',
            'path': [
                'generateRocketChatToken'
            ]
        }
    ]
}

snapshots['TestRocketchat::test_generate_rocket_chat_token_exception_debug 1'] = {
    'data': {
        'generateRocketChatToken': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 11,
                    'line': 3
                }
            ],
            'message': 'Failed to generate Rocketchat token for user: testuser',
            'path': [
                'generateRocketChatToken'
            ]
        }
    ]
}
