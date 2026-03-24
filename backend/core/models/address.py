"""
Location and Address Models
"""

import uuid
from functools import lru_cache
from typing import List

from django.contrib.contenttypes.models import ContentType
from django.db import models
from .common import Tracking


class AddressManager(models.Manager):
    pass


class Address(Tracking):
    """
    House Number, Street Direction, Street Name, Street Suffix, City, State, Zip, Country
    see: https://github.com/mirumee/google-i18n-address
    """

    objects = AddressManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    address_line_one = models.CharField(max_length=250, blank=True)
    address_line_two = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=256, blank=True)
    state = models.CharField(max_length=100, blank=True)
    street = models.CharField(max_length=500, blank=True)
    zipcode = models.CharField(max_length=20, blank=True)

    class Meta:
        permissions = (
            ('view_address_line_one', 'Can view address_line_one field'),
            ('change_address_line_one', 'Can change address_line_one field'),
            ('view_address_line_two', 'Can view address_line_two field'),
            ('change_address_line_two', 'Can change address_line_two field'),
            ('view_city', 'Can view city field'),
            ('change_city', 'Can change city field'),
            ('view_state', 'Can view state field'),
            ('change_state', 'Can change state field'),
            ('view_street', 'Can view street field'),
            ('change_street', 'Can change street field'),
            ('view_zipcode', 'Can view zipcode field'),
            ('change_zipcode', 'Can change zipcode field'),
        )

    @classmethod
    @lru_cache()
    def whitelist_fields(cls) -> List[str]:
        from core.models.permissions import ApprovalPropertyWhitelist
        return list(
            ApprovalPropertyWhitelist.objects.filter(
                content_type=ContentType.objects.get_for_model(cls),
                enabled=True
            ).values_list('attribute', flat=True)
        )

    def to_search(self):
        return f'{self.street} {self.city} {self.state} {self.zipcode}'

    def __str__(self):
        return f'{self.street} {self.city} {self.state} {self.zipcode}'
