"""
auth1.middleware for supporting login with Session token.
"""
from importlib import import_module
from typing import Optional

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse


class Auth0SessionMiddlewareException(BaseException, HttpResponse):

    def __init__(self, content=b"", *args, **kwargs):
        BaseException.__init__(self)
        HttpResponse.__init__(self, content, *args, **kwargs)


class Auth0SessionMiddleware(SessionMiddleware):
    """
    Session middleware for Session token based authentication.
    """

    AUTHORIZATION = 'Authorization'
    BEARER = 'Bearer'
    SESSION = 'Session'

    def __init__(self, get_response):
        super().__init__(get_response)
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore
        self._process_request_chain = [
            self._pull_from_authorization_session,
            self._pull_from_authorization_bearer,
        ]

    @classmethod
    def _get_authorization_data(cls, request: WSGIRequest, schema) -> Optional[str]:
        if cls.AUTHORIZATION not in request.headers:
            return None
        parts = request.headers[cls.AUTHORIZATION].split(' ')
        if len(parts) != 2:
            return None
        kind, token = parts
        if kind == schema:
            return token
        return None

    def _pull_from_authorization_bearer(self, request: WSGIRequest) -> Optional[bool]:
        api_key = self._get_authorization_data(request, self.BEARER)
        if api_key:
            if api_key == settings.CLIENT_SESSION_API_KEY:
                request.session = self.SessionStore()
                request.session.clear()
                return True
            else:
                raise Auth0SessionMiddlewareException('Unauthorized', status=401)

    def _pull_from_authorization_session(self, request: WSGIRequest) -> Optional[bool]:
        session_key = self._get_authorization_data(request, self.SESSION)
        if session_key:
            request.session = self.SessionStore(session_key)
            if request.session.exists(session_key):
                return True
            else:
                raise Auth0SessionMiddlewareException('Unauthorized', status=401)

    def process_request(self, request: WSGIRequest):
        """
        Verifies if the session token is valid.
        """
        try:
            for handler in self._process_request_chain:
                if handler(request):
                    break
        except Auth0SessionMiddlewareException as response:
            return response

    def process_response(self, request: WSGIRequest, response: HttpResponse):
        api_key = self._get_authorization_data(request, self.BEARER)
        if api_key and api_key == settings.CLIENT_SESSION_API_KEY:
            response.headers[self.AUTHORIZATION] = f'{self.SESSION} {request.session.session_key}'
        return response
