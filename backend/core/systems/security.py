import dataclasses

from config.permissions import AbstractPermissions
from django.db import models


class Security:

    @dataclasses.dataclass
    class ModelPermissions:
        model = models.Model
        permissions: list[AbstractPermissions] = None
        permissions_map: dict[str, AbstractPermissions] = dataclasses.field(default_factory=dict)

        def __post_init__(self):
            from core.models import BaseCoreModel
            model: BaseCoreModel = self.model
            self.permissions_map = {**model.permissions()}
            self.permissions = list(self.permissions_map.values())

        def view(self, user):
            return self.permissions_map['view'].check(user)

        def add(self, user):
            return self.permissions_map['add'].check(user)

        def change(self, user):
            return self.permissions_map['change'].check(user)

        def delete(self, user):
            return self.permissions_map['delete'].check(user)
