"""UtilityForm — Django form utility for nested upsert mutations.

Preserved from the original Graphene implementation, with Graphene-specific
imports replaced by Strawberry equivalents.
"""
import logging

from django.core.exceptions import ValidationError
from django.forms import FileField, ModelChoiceField, ModelForm
from graphql import GraphQLError

from core.schema.common import GlobalIDUtils

logger = logging.getLogger(__name__)


class UtilityForm:
    form_map = {}

    def pre_save(self, data):
        return data

    def post_save(self, data):
        return self.instance

    @classmethod
    def register_form(cls, input_class, form_class):
        cls.form_map[str(input_class)] = form_class

    @classmethod
    def _apply_forms_to_fields(cls, root, info, input, parent=None):
        if isinstance(input, dict):
            for key, value in input.items():
                if isinstance(value, list):
                    new_value = []
                    for v in value:
                        instance = cls._apply_form(root, info, v, key, None)
                        new_value.append(instance.pk) if instance else v
                    input[key] = new_value
                else:
                    instance = cls._apply_form(root, info, value, key, parent)
                    if instance is not None:
                        input[key] = instance.pk

    @classmethod
    def _apply_form(cls, root, info, input, key=None, parent=None):
        form_class = cls.form_map.get(str(type(input)), None)
        if not form_class:
            return None

        instance = cls.get_instance(info, input, key, parent)
        input['id'] = instance.pk if instance else None
        cls._apply_forms_to_fields(root, info, input, instance)
        form = form_class(data=input, instance=instance)
        setattr(form, 'info', info)

        if form.is_valid():
            instance = form.save()
            instance = form.post_save(input)
            return instance
        else:
            raise ValidationError(form.errors)

    @classmethod
    def get_instance(cls, info, input, key, parent):
        pk = input.get('id', None)
        if pk and isinstance(pk, str):
            obj = GlobalIDUtils.find_object_by_global_id(pk, raise_not_found=True)
            return obj
        elif parent and key:
            attr = getattr(parent, key, None)
            is_single = getattr(attr, "filter", None) is None
            if is_single:
                return attr
        elif pk and isinstance(pk, int):
            raise GraphQLError('GlobalID is required for update')

        return None

    @classmethod
    def apply_forms(cls, root, info, input):
        return cls._apply_form(root, info, input)

    @classmethod
    def db_key(cls, model, global_id):
        pk = GlobalIDUtils.get_pk_flexible(global_id)
        return pk if pk else global_id

    def _clean_fields(self):
        for name, bf in self._bound_items():
            field = bf.field
            value = bf.initial if field.disabled else bf.data
            try:
                if isinstance(field, FileField):
                    value = field.clean(value, bf.initial)
                elif isinstance(field, ModelChoiceField) and bf.initial:
                    value = field.queryset.get(pk=bf.initial)
                elif value is None:
                    value = bf.initial
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, "clean_%s" % name):
                    value = getattr(self, "clean_%s" % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)

    def full_clean(self: ModelForm):
        for name, field in self.fields.items():
            if hasattr(field, 'to_field_name'):
                key = field.to_field_name or 'pk'
                if (key == 'id' or key == 'pk') and name in self.data:
                    value = self.data[name]
                    if isinstance(value, list):
                        value = [cls.db_key(field.queryset.model, v) for v in value]
                    elif isinstance(value, str):
                        value = cls.db_key(field.queryset.model, value)

                    self.data[name] = value

        return super().full_clean()

    def clean(self):
        if any(self.errors):
            return

        return super().clean()
