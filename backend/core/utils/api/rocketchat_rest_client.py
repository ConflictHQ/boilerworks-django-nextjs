import hashlib
import logging
import random
import string

from config import settings
from core.models import Profile
from core.utils.request_handler import RequestHandler
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class RocketchatRestClient:
    request_handler = RequestHandler()

    def __init__(self):
        self.server_url = settings.ROCKETCHAT_URL + '/api/v1/'
        self.admin_headers = {
            'X-User-Id': settings.ROCKETCHAT_API_USER_ID,
            'X-Auth-Token': settings.ROCKETCHAT_API_AUTH_TOKEN
        }
        self.ssl_verify = False

    def _generate_token(cls, n=50):
        chars = string.ascii_letters + string.digits
        token = ''.join(random.SystemRandom().choice(chars) for _ in range(n))
        token = hashlib.sha3_512(token.encode()).hexdigest()
        return token

    def create_user(self, user: User):
        profile: Profile = user.profile
        if not profile.rocket_id:
            body = {
                'email': user.email,
                'name': f'{user.first_name} {user.last_name}',
                'password': self._generate_token(),
                'username': user.username,
                'customFields': {
                    'profile': str(user.profile.pk),
                }
            }
            response = self.request_handler.make_request(
                method='POST',
                url=self.server_url + 'users.create',
                headers=self.admin_headers,
                json=body
            )

            if response.get('success', False) is False:
                msg = f'Failed to create Rocketchat user: {user.username}'
                logger.error(f'{msg}. {response}')
                raise Exception(f'{msg}. {response}') if settings.DEBUG else Exception(msg)
            profile.rocket_id = response['user']['_id']
            profile.save()

    def update_user(self, user: User):
        profile: Profile = user.profile
        if not profile.rocket_id:
            self.create_user(user)
        else:
            body = {
                "userId": profile.rocket_id,
                "data": {
                    'name': f'{user.first_name} {user.last_name}',
                    'username': user.username
                }
            }
            response = self.request_handler.make_request(
                method='POST',
                url=self.server_url + 'users.update',
                headers=self.admin_headers,
                json=body
            )

            if response.get('success', False) is False:
                msg = f'Failed to update Rocketchat user: {user.username}'
                logger.error(f'{msg}. {response}')
                raise Exception(f'{msg}. {response}') if settings.DEBUG else Exception(msg)

    def create_auth_token(self, user: User) -> str:
        self.create_user(user)

        response = self.request_handler.make_request(
            method='POST',
            url=self.server_url + 'users.createToken',
            headers=self.admin_headers,
            json={
                'userId': user.profile.rocket_id
            }
        )
        if response.get('success', False) is False:
            msg = f'Failed to generate Rocketchat token for user: {user.username}'
            logger.error(f'{msg}. {response}')
            raise Exception(f'{msg}. {response}') if settings.DEBUG else Exception(msg)
        return response['data']['authToken']

    def read_channel(self, chat_identifier: str):
        response = self.request_handler.make_request(
            method='GET',
            url=self.server_url + 'channels.history',
            headers=self.admin_headers,
            params={
                'roomName': chat_identifier
            }
        )

        return response.get('messages', [])
