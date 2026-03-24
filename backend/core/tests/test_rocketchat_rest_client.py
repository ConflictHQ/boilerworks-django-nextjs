from unittest.mock import patch

import pytest
from core.tests.utils.base_test import BaseTest
from core.utils.api.rocketchat_rest_client import RocketchatRestClient
from core.utils.request_handler import RequestHandler
from django.contrib.auth.models import User
from django.test import override_settings


class TestRocketchatRestClient(BaseTest):
    def setUp(self):
        super().setUp()
        bmiranda, _ = User.objects.get_or_create(username='bmiranda')
        from core.models import Profile
        profile, _ = Profile.objects.get_or_create(user=bmiranda)
        profile.rocket_id = 'existing_rocket_id'
        profile.save()

    @patch.object(RequestHandler, 'make_request')
    def test_generate_rocket_chat_token(self, mock_make_request):
        expected_token = 'tokent'
        mock_make_request.return_value = {
            'success': True,
            'data': {
                'authToken': expected_token
            }
        }
        #  User bmiranda already has a rocketchat id/account
        user = User.objects.filter(username='bmiranda').first()
        assert user
        response = RocketchatRestClient().create_auth_token(user)
        assert response == expected_token

    @patch.object(RequestHandler, 'make_request')
    def test_generate_rocket_chat_token_new_account(self, mock_make_request):
        expected_token = 'token'
        expected_id = 'new_id'
        mock_make_request.side_effect = [
            {
                'success': True,
                'user': {
                    '_id': expected_id
                }
            },
            {
                'success': True,
                'data': {
                    'authToken': expected_token
                }
            }
        ]
        response = RocketchatRestClient().create_auth_token(self.user)
        assert self.user.profile.rocket_id == expected_id
        assert response == expected_token

    @override_settings(DEBUG=True)
    @patch.object(RequestHandler, 'make_request')
    def test_generate_rocket_chat_token_exception_debug_mode(self, mock_make_request):
        response = {
            'success': False,
            'error': 'Not authorized [error-not-authorized]',
            'errorType': 'error-not-authorized',
            'details': {
                'method': 'create'
            }
        }
        mock_make_request.return_value = response
        with pytest.raises(Exception) as exc:
            RocketchatRestClient().create_auth_token(self.user)
        assert exc.value.args[0] == f'Failed to create Rocketchat user: testuser. {response}'
