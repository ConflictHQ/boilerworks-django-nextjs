# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['ProfileTest::test_get_current_user_profile 1'] = {
    'data': {
        'me': {
            'profile': {
                'address': None,
                'emergencyContactName': None,
                'emergencyPhoneNumber': None,
                'firstName': None,
                'lastName': None,
                'phoneNumber': None,
                'preferredContact': None
            }
        }
    }
}

snapshots['ProfileTest::test_upsert_current_user_profile 1'] = {
    'data': {
        'profile': {
            'errors': [
            ],
            'ok': True
        }
    }
}

snapshots['ProfileTest::test_upsert_current_user_profile_fails_serialization 1'] = {
    'data': {
        'profile': {
            'errors': [
                {
                    'field': 'phoneNumber',
                    'messages': [
                        'The phone number entered is not valid.'
                    ]
                },
                {
                    'field': 'emergencyPhoneNumber',
                    'messages': [
                        'The phone number entered is not valid.'
                    ]
                }
            ],
            'ok': False
        }
    }
}

snapshots['ProfileTest::test_upsert_profile_for_given_user_fails_serialization 1'] = {
    'data': {
        'profile': {
            'errors': [
                {
                    'field': 'address.zipcode',
                    'messages': [
                        'Ensure this field has no more than 10 characters.'
                    ]
                },
                {
                    'field': 'user.email',
                    'messages': [
                        'Enter a valid email address.'
                    ]
                },
                {
                    'field': 'phoneNumber',
                    'messages': [
                        'The phone number entered is not valid.'
                    ]
                },
                {
                    'field': 'emergencyPhoneNumber',
                    'messages': [
                        'The phone number entered is not valid.'
                    ]
                }
            ],
            'ok': False
        }
    }
}

snapshots['UserTest::test_get_current_user 1'] = {
    'data': {
        'me': {
            'email': '',
            'firstName': '',
            'isActive': True,
            'lastName': '',
            'username': 'testuser'
        }
    }
}

snapshots['UserTest::test_get_user_by_id 1'] = {
    'data': {
        'user': {
            'firstName': '',
            'id': 'VXNlclR5cGU6Mg==',
            'lastName': '',
            'username': 'testuser'
        }
    }
}

snapshots['UserTest::test_get_users_filtered_by_search 1'] = {
    'data': {
        'users': {
            'edges': [
                {
                    'node': {
                        'firstName': '',
                        'id': 'VXNlclR5cGU6Mg==',
                        'username': 'testuser'
                    }
                }
            ],
            'totalCount': 1
        }
    }
}
