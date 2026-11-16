"""Superset REST client: service-account login, guest tokens and embedding.

All calls are server to server. The service account's credentials and access
token never leave the backend; the browser only receives guest tokens.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 15


class SupersetError(Exception):
    """Superset is unreachable, misconfigured or refused the request."""


class SupersetRestClient:

    def __init__(self):
        if not settings.SUPERSET_URL:
            raise SupersetError('Superset is not configured (SUPERSET_URL is empty)')
        self.server_url = settings.SUPERSET_URL.rstrip('/')
        self.session = requests.Session()
        self._logged_in = False

    def _send(self, method, path, what, **kwargs):
        try:
            response = self.session.request(method, f'{self.server_url}{path}', timeout=TIMEOUT, **kwargs)
        except requests.RequestException as error:
            raise SupersetError(f'Superset {what} failed: {error.__class__.__name__}') from error
        self._raise_for_status(response, what)
        return response.json()

    def _login(self):
        """Sign in as the service account and pick up a CSRF token for writes."""
        token = self._send('POST', '/api/v1/security/login', 'login', json={
            'username': settings.SUPERSET_USERNAME,
            'password': settings.SUPERSET_PASSWORD,
            'provider': 'db',
            'refresh': False,
        })['access_token']
        self.session.headers['Authorization'] = f'Bearer {token}'
        self.session.headers['X-CSRFToken'] = self._send('GET', '/api/v1/security/csrf_token/', 'csrf token')['result']
        self.session.headers['Referer'] = self.server_url
        self._logged_in = True

    def _request(self, method, path, what, **kwargs):
        if not self._logged_in:
            self._login()
        return self._send(method, path, what, **kwargs)

    @staticmethod
    def _raise_for_status(response, what):
        if response.status_code >= 400:
            # Log Superset's message, never the request (it can carry credentials).
            logger.error(f'Superset {what} failed: HTTP {response.status_code} {response.text[:500]}')
            raise SupersetError(f'Superset {what} failed (HTTP {response.status_code})')

    def guest_token(self, embedded_id, user, rls=None):
        """Issue a guest token for one embedded dashboard, scoped by `rls`."""
        payload = {
            'user': {
                'username': user.get_username(),
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
            },
            'resources': [{'type': 'dashboard', 'id': str(embedded_id)}],
            'rls': rls or [],
        }
        return self._request('POST', '/api/v1/security/guest_token/', 'guest token', json=payload)['token']

    def enable_embedding(self, dashboard_id_or_slug, allowed_domains):
        """Turn on embedding for a dashboard and return its embedded UUID and title."""
        dashboard = self._request('GET', f'/api/v1/dashboard/{dashboard_id_or_slug}', 'dashboard lookup')['result']
        embedded = self._request(
            'POST', f"/api/v1/dashboard/{dashboard['id']}/embedded", 'enable embedding',
            json={'allowed_domains': list(allowed_domains)},
        )['result']
        return embedded['uuid'], dashboard['dashboard_title']
