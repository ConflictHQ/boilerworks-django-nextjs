from unittest.mock import MagicMock

from auth1.sessions import Auth1SessionWorkflow
from core.tests.utils.base_test import BaseTest
from django.contrib.auth.models import User


class SessionsTest(BaseTest):

    def setUp(self):
        super().setUp()
        User.objects.get_or_create(
            username='sessions_test_user',
            defaults={'email': 'testuser@boilerworks.dev'},
        )

    def _make_user_info(self, email):
        user_info = MagicMock()
        user_info.email = email
        return user_info

    def test_lookup_user_find_user_by_email(self):
        email = 'testuser@boilerworks.dev'
        user = Auth1SessionWorkflow._lookup_user(self._make_user_info(email))
        self.assertEqual(user.email, email)

    def test_lookup_user_find_user_by_email_with_caps(self):
        email = 'TestUser@boilerworks.dev'
        user = Auth1SessionWorkflow._lookup_user(self._make_user_info(email))
        self.assertEqual(user.email, email.lower())

    def test_lookup_user_dont_find_unknown_user(self):
        user = Auth1SessionWorkflow._lookup_user(self._make_user_info('unknown@boilerworks.dev'))
        self.assertIsNone(user)
