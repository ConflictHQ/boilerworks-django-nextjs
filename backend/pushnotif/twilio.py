import json
import logging

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from twilio.base.values import unset
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.rest.api.v2010.account.message import MessageInstance

logger = logging.getLogger(__name__)


class TwilioService:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_SID,
            settings.TWILIO_SECRET
        )
        self.from_number = settings.TWILIO_FROM_NUMBER

    @classmethod
    def status_callback_url(cls):
        return settings.TWILIO_CALLBACK

    @classmethod
    def status_callback(cls, request: WSGIRequest):
        validator = RequestValidator(settings.TWILIO_SECRET)
        twilio_signature = request.headers.get('X-Twilio-Signature', '')
        body = request.POST

        if not validator.validate(cls.status_callback_url(), body, twilio_signature):
            return HttpResponse(json.dumps({'message': 'Invalid request'}), status=400)

        message_sid = body.get('MessageSid')
        status = body.get('MessageStatus')

        from pushnotif.models import SMSNotification
        notification = SMSNotification.objects.filter(sid=message_sid).first()
        notification.save()
        notification.update_status(status=status)
        return HttpResponse(json.dumps({"response": "accepted"}), status=202)

    @classmethod
    def urls(cls):
        """
        Provides the list of urls supported this workflow:

        - status_callback: status callback.
        """
        return [
            path("status_callback", csrf_exempt(cls.status_callback), name="status_callback"),
        ]

    def send_sms(self, to_number: str, message: str) -> MessageInstance:
        status_callback_url = self.status_callback_url()
        if not status_callback_url:
            status_callback_url = unset
        return self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to_number,
            status_callback=status_callback_url,
            provide_feedback=True,
        )
