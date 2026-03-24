from __future__ import annotations

from typing import Optional

import strawberry_django
from strawberry.types import Info

from core.models import Address


@strawberry_django.type(Address)
class AddressType:
    """Address with field-level permission checks."""

    @strawberry_django.field
    def address_line_one(self, info: Info) -> str:
        if Address.p('address_line_one').view.by(info.context.user):
            return self.address_line_one
        return ""

    @strawberry_django.field
    def address_line_two(self, info: Info) -> str:
        if Address.p('address_line_two').view.by(info.context.user):
            return self.address_line_two
        return ""

    @strawberry_django.field
    def city(self, info: Info) -> str:
        if Address.p('city').view.by(info.context.user):
            return self.city
        return ""

    @strawberry_django.field
    def state(self, info: Info) -> str:
        if Address.p('state').view.by(info.context.user):
            return self.state
        return ""

    @strawberry_django.field
    def street(self, info: Info) -> str:
        if Address.p('street').view.by(info.context.user):
            return self.street
        return ""

    @strawberry_django.field
    def zipcode(self, info: Info) -> str:
        if Address.p('zipcode').view.by(info.context.user):
            return self.zipcode
        return ""
