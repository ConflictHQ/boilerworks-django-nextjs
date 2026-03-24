import threading
from typing import Optional

from django.contrib.auth.models import User

# Thread-local storage for the current user
_user_storage = threading.local()


class CurrentUserMiddleware:
    """
    Middleware to store the current user in thread-local storage
    so it can be accessed in signals and other places where
    request context is not available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user in thread-local storage
        set_current_user(getattr(request, 'user', None))

        try:
            response = self.get_response(request)
        finally:
            # Clean up thread-local storage
            clear_current_user()

        return response


def set_current_user(user: Optional[User]):
    """Set the current user in thread-local storage."""
    _user_storage.user = user


def get_current_user() -> Optional[User]:
    """Get the current user from thread-local storage."""
    return getattr(_user_storage, 'user', None)


def clear_current_user():
    """Clear the current user from thread-local storage."""
    if hasattr(_user_storage, 'user'):
        delattr(_user_storage, 'user')
