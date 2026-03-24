import logging

import firebase_admin
from django.conf import settings
from firebase_admin import messaging
from firebase_admin.credentials import Certificate
from firebase_admin.messaging import Message

logger = logging.getLogger(__name__)


class Firebase:

    def __new__(cls, *args, **kwargs):
        key = '_instance'
        """
        Singleton Pattern to avoid create
        """
        if not hasattr(cls, key):
            obj = super().__new__(cls)
            setattr(cls, key, obj)
            certificate = Certificate(settings.FIREBASE_ADMIN_SDK)
            firebase_admin.initialize_app(certificate)
        return getattr(cls, key)

    def send(self, message: Message):
        return messaging.send_each_for_multicast(message)
