from unittest.mock import patch

from core.tests.utils.base_test import BaseTest
from core.utils.api.rocketchat_rest_client import RocketchatRestClient
from django.test import override_settings


class TestRocketchat(BaseTest):
    def setUp(self):
        super().setUp()
        self.mock_token_data = 'abc'

    @patch.object(RocketchatRestClient, 'create_auth_token')
    def test_generate_rocket_chat_token(self, mock_create_auth_token):
        """
        # Requests rocket chat token for login
        Creates rocket chat token for a user,
         if the user does not have a rocket chat account it is created as part of the same request.
        :return: the authentication token to be used for the rocket chat
        """
        mock_create_auth_token.return_value = self.mock_token_data
        request = self.request()

        query = '''
        mutation CreateRocketchatTokenMutation{
          generateRocketChatToken {
            token
          }
        }
        '''
        variables = {}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    @patch.object(RocketchatRestClient, 'create_auth_token')
    def test_generate_rocket_chat_token_exception(self, mock_create_auth_token):
        """
        # Requests rocket chat token for login
        Creates rocket chat token for a user,
         if the user does not have a rocket chat account it is created as part of the same request.
        :return: the authentication token to be used for the rocket chat
        """
        mock_create_auth_token.side_effect = Exception(
            f'Failed to generate Rocketchat token for user: {self.user.username}'
        )
        request = self.request()

        query = '''
        mutation CreateRocketchatTokenMutation{
          generateRocketChatToken {
            token
          }
        }
        '''
        variables = {}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryError(query, variables, response)

    @override_settings(DEBUG=True)
    @patch.object(RocketchatRestClient, 'create_auth_token')
    def test_generate_rocket_chat_token_exception_debug(self, mock_create_auth_token):
        """
        # Requests rocket chat token for login
        Creates rocket chat token for a user,
         if the user does not have a rocket chat account it is created as part of the same request.
        :return: the authentication token to be used for the rocket chat
        """
        mock_create_auth_token.side_effect = Exception(
            f'Failed to generate Rocketchat token for user: {self.user.username}'
        )
        request = self.request()

        query = '''
        mutation CreateRocketchatTokenMutation{
          generateRocketChatToken {
            token
          }
        }
        '''
        variables = {}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryError(query, variables, response)
