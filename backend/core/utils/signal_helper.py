import dataclasses
import logging
from itertools import chain
from typing import Type

from django.db import models
from django.db.models import signals
from django.db.models.fields.related_descriptors import ManyToManyDescriptor

logger = logging.getLogger(__name__)


class SignalChoices(models.TextChoices):
    custom = 'custom', None
    pre_init = 'pre_init', signals.pre_init
    post_init = 'post_init', signals.post_init
    pre_save = 'pre_save', signals.pre_save
    post_save = 'post_save', signals.post_save
    pre_delete = 'pre_delete', signals.pre_delete
    post_delete = 'post_delete', signals.post_delete
    m2m_changed = 'm2m_changed', signals.m2m_changed
    pre_migrate = 'pre_migrate', signals.pre_migrate
    post_migrate = 'post_migrate', signals.post_migrate

    def __new__(cls, value, signal, *args, **kwargs):
        obj = str.__new__(cls, *args, **kwargs)
        obj._value_ = value
        obj.signal = signal
        return obj


@dataclasses.dataclass
class ModelSignal:
    model: Type[models.Model]
    signal: SignalChoices
    callback: callable

    def connect(self):
        self.signal.signal.connect(self._callback, sender=self.model)

    def disconnect(self):
        self.signal.signal.disconnect(self._callback, sender=self.model)

    def _callback(self, **kwargs):
        try:
            self.callback(**kwargs)
        except Exception as e:
            logger.exception(f'Error in signal {self} callback: {e}')


@dataclasses.dataclass
class ModelSignalHelper:
    """
    Helper class for connecting and disconnecting signals for a model
    Two ways to use this class:
    1. Subclass this class and override the signal methods
    2. Instantiate this class and pass the callback functions to the listen methods
    """
    name: str
    model: Type[models.Model]
    description: str = None
    _connection: bool = False
    _signals: dict = dataclasses.field(default_factory=dict)
    _m2m_signals: dict = dataclasses.field(default_factory=dict)

    def listen(self, signal: SignalChoices, callback):
        if not isinstance(signal, SignalChoices) and isinstance(signal, str):
            signal = SignalChoices[signal]

        if signal in self._signals:
            if self._signals[signal].callback != callback:
                if self._connection:
                    self._signals[signal].disconnect()
            else:
                logger.info(f'Callback for signal {signal} already registered for {self.model}')
                return self

        self._signals[signal] = ModelSignal(self.model, signal, callback)
        if self._connection:
            self._signals[signal].connect()
        return self

    def listen_pre_init(self, callback=None):
        return self.listen(SignalChoices.pre_init, callback=callback or self.pre_init)

    def listen_post_init(self, callback=None):
        return self.listen(SignalChoices.post_init, callback=callback or self.post_init)

    def listen_pre_save(self, callback=None):
        return self.listen(SignalChoices.pre_save, callback=callback or self.pre_save)

    def listen_post_save(self, callback=None):
        return self.listen(SignalChoices.post_save, callback=callback or self.post_save)

    def listen_pre_delete(self, callback=None):
        return self.listen(SignalChoices.pre_init, callback=callback or self.pre_delete)

    def listen_post_delete(self, callback=None):
        return self.listen(SignalChoices.post_init, callback=callback or self.post_delete)

    def listen_m2m_changed(self, m2m_field: ManyToManyDescriptor, callback=None):
        assert m2m_field.field == self.model._meta.get_field(m2m_field.field.name), f'{m2m_field} does not belong to {self.model}'
        assert isinstance(m2m_field.field, models.ManyToManyField), f'{m2m_field} is not a ManyToManyField'

        through = m2m_field.through
        if through in self._m2m_signals:
            if self._m2m_signals[through].callback != callback:
                self._m2m_signals[through].unregister()
            else:
                logger.info(f'Callback for signal {SignalChoices.m2m_changed} already registered for {self.model}')
                return self

        self._m2m_signals[through] = ModelSignal(through, SignalChoices.m2m_changed, callback or self.m2m_changed)
        if self._connection:
            self._m2m_signals[through].connect()
        return self

    def listen_pre_migrate(self, callback=None):
        return self.listen(SignalChoices.pre_migrate, callback=callback or self.pre_migrate)

    def listen_post_migrate(self, callback=None):
        return self.listen(SignalChoices.post_migrate, callback=callback or self.post_migrate)

    def pre_init(self, instance, **kwargs):
        logger.warning(f'pre_init signal not implemented for {self.name}')

    def post_init(self, instance, **kwargs):
        logger.warning(f'post_init signal not implemented for {self.name}')

    def pre_save(self, instance, **kwargs):
        logger.warning(f'pre_save signal not implemented for {self.name}')

    def post_save(self, instance, created, **kwargs):
        logger.warning(f'post_save signal not implemented for {self.name}')

    def pre_delete(self, instance, **kwargs):
        logger.warning(f'pre_delete signal not implemented for {self.name}')

    def post_delete(self, instance, **kwargs):
        logger.warning(f'post_delete signal not implemented for {self.name}')

    def m2m_changed(self, sender, instance, action, model, pk_set, **kwargs):
        logger.warning(f'm2m_changed signal not implemented for {self.name}')

    def pre_migrate(self, instance, **kwargs):
        logger.warning(f'pre_migrate signal not implemented for {self.name}')

    def post_migrate(self, instance, **kwargs):
        logger.warning(f'post_migrate signal not implemented for {self.name}')

    def connect(self):
        for signal in chain(self._signals.values(), self._m2m_signals.values()):
            signal.connect()
        self._connection = True

    def disconnect(self):
        for signal in chain(self._signals.values(), self._m2m_signals.values()):
            signal.disconnect()
        self._connection = False
