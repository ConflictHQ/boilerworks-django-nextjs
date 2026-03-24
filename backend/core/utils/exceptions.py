import dataclasses

from django.core.exceptions import ValidationError
from django.db.models import Field
from django.db.models.query_utils import DeferredAttribute


@dataclasses.dataclass
class ValidationErrorBuilder:
    """
    Helper class to build validation errors.
    It allows to chain multiple validations and raise them all at once.
    """

    params: dict = dataclasses.field(default_factory=dict)
    _on_error: bool = False

    def check(self, condition):
        self._on_error = condition
        return self

    def validate(self, field, message, code=None):
        if self._on_error:
            if isinstance(field, DeferredAttribute):
                field = field.field.attname
            elif isinstance(field, Field):
                field = field.attname

            if field in self.params:
                self.params[field].message += f'\n{message}'
            else:
                self.params[field] = ValidationError(message, code)
        return self

    def raise_error(self):
        if self.params:
            raise ValidationError(self.params)
