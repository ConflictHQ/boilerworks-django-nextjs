import dataclasses

from core.models import SignRequest
from core.tests.utils.base_test import BaseTest
from core.utils.signal_helper import ModelSignalHelper
from django.contrib.auth.models import User


@dataclasses.dataclass
class SignRequestSignals(ModelSignalHelper):
    pre_save_called: bool = False
    m2m_changed_called: bool = False

    def pre_save(self, instance, **kwargs):
        self.pre_save_called = True

    def m2m_changed(self, sender, instance, action, model, pk_set, **kwargs):
        self.m2m_changed_called = True


class SignalHelperTest(BaseTest):

    def test_connection(self):
        signal = SignRequestSignals('my signal', SignRequest, description='my description')
        signal.listen_pre_save()

        signal.connect()

        SignRequest.objects.create()

        self.assertEqual(signal.name, 'my signal')
        self.assertEqual(signal.model, SignRequest)
        self.assertTrue(signal._connection)
        self.assertEqual(signal.description, 'my description')
        self.assertEqual(len(signal._signals), 1)
        self.assertTrue(signal.pre_save_called)

    def test_disconnection(self):
        signal = SignRequestSignals('my signal', SignRequest, description='my description')
        signal.listen_pre_save()

        signal.connect()
        signal.disconnect()

        SignRequest.objects.create()

        self.assertEqual(signal.model, SignRequest)
        self.assertFalse(signal._connection)
        self.assertFalse(signal.pre_save_called)

    def test_m2m_connection(self):
        signal = SignRequestSignals('my signal', SignRequest, description='my description')

        signal.listen_m2m_changed(SignRequest.sign_requested)
        signal.connect()

        sign = SignRequest.objects.create()
        sign.sign_requested.add(User.objects.first())

        self.assertTrue(signal._connection)
        self.assertEqual(len(signal._m2m_signals), 1)
        self.assertTrue(signal.m2m_changed_called)
