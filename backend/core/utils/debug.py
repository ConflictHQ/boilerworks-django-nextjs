import logging
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def autologin(view_func):
    """
    Temporal solution for login user.
    """
    def wrapped_view(*args, **kwargs):
        if settings.DEBUG and args[0].user.is_anonymous:
            user = get_user_model().objects.filter(username=settings.DEFAULT_USER_TEST).first()
            if not user:
                raise PermissionDenied('User is not authenticated')
            args[0].user = user
        elif args[0].user.is_anonymous:
            raise PermissionDenied('User is not authenticated')

        result = view_func(*args, **kwargs)
        return result

    return wraps(view_func)(wrapped_view)
