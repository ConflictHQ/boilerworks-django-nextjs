import enum
import logging
from collections import namedtuple
from typing import Type

import pydash
from core.fields import HashField
from django.apps import AppConfig
from django.db import DatabaseError, models
from django.db.models import Field, Model
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)

__all__ = [
    'EnumModel',
    'EnumModelBase',
    'check_model_if_is_ready',
    'register_for_model',
]


class EnumModelBase(models.base.ModelBase):

    def __new__(cls, name, bases, attrs, **kwargs):

        meta = "Meta"
        if meta in attrs and attrs[meta].abstract:
            return models.base.ModelBase.__new__(cls, name, bases, attrs, **kwargs)

        field_names: list[str] = []
        for attr_name, attr in attrs.items():
            match attr:
                case Field():
                    field_names.append(attr_name)

        attrs["Literal"] = namedtuple(name, list(field_names))
        new_class = models.base.ModelBase.__new__(cls, name, bases, attrs, **kwargs)

        return new_class


class EnumModel(models.Model, metaclass=EnumModelBase):
    class Meta:
        abstract = True
        ordering = 'ordinal',

    name = models.CharField(max_length=64, primary_key=True)
    ordinal = models.IntegerField(null=False, blank=False, default=0, db_index=True)
    hashcode = HashField()

    Literal: Type[tuple]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class BaseEnumModel(enum.Enum):
    """
    Base Enum Model for creating instances in the database
    """

    Model: Type[Model]

    @classmethod
    def register(cls, app: AppConfig):
        """
        Register the given member as a model instance in the database
        """
        if not check_model_if_is_ready(cls.Model):
            logger.warning(f'Model is not ready: {cls.__name__}')
            return

        logger.debug(f'Registering Enum: {cls.__name__}')

        try:
            count = cls.Model.objects.exclude(
                name__in=[member.identifier for member in cls]
            ).count()
            if count:
                logger.debug(f'There are {count} members in the that are not in use')
        except DatabaseError:
            logger.debug('Unable to register')

        for ordinal, member_instance in enumerate(cls):
            member_instance: BaseEnumModel = member_instance
            name: str = member_instance.identifier
            hashcode: int = HashField.hash(ordinal)
            queryset = cls.Model.objects.filter(name=name)
            values = member_instance.value._asdict()

            for key, value in sorted(values.items()):
                match key:
                    case "hashcode":
                        continue
                    case _:
                        hashcode ^= HashField.hash(key)
                        hashcode ^= HashField.hash(value)

            values['name'] = member_instance.identifier
            values['ordinal'] = ordinal
            values['hashcode'] = hashcode

            if queryset.exists():
                if queryset.filter(hashcode=hashcode).exists():
                    logger.debug(f'No need to update object {cls.__name__}.{name}')
                else:
                    logger.info(f'Updating: {cls.__name__}.{name} {hashcode}')
                    queryset.update(**values)
            else:
                instance = cls.Model(**values)
                instance.save()
            member_instance.member_register()

    @cached_property
    def identifier(self) -> str:
        """
        Returns the identifier of this member in the database
        """
        return pydash.capitalize(self.name)

    @cached_property
    def instance(self):
        return self.Model.objects.filter(name=self.identifier).first()

    def member_register(self):
        """
        Creates any additional data in the database after migration
        """
        logger.debug(f'{self.name}: registered')


def check_model_if_is_ready(*models: Type[Model]) -> bool:
    """
    Verifies that the given models can be accessed
    """
    try:
        for model in models:
            model.objects.count()
        return True
    except DatabaseError:
        logger.info(f"{model._meta.model_name} is not ready to create objects")
        return False


def register_for_model(model: Type[EnumModel]):
    """
    Registers a model in the database for the given enum
    """

    assert issubclass(model, EnumModel)

    def decorator(enumeration: Type[enum.Enum]):
        assert issubclass(enumeration, BaseEnumModel)
        setattr(enumeration, 'Model', model)
        return enumeration

    return decorator
