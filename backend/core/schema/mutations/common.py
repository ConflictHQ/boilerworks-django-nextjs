import logging

import graphene
from core.schema.common import DjangoObjectTypeUtils
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import FileField, ModelChoiceField, ModelForm
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django.types import ErrorType
from graphql import GraphQLError

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
            return DjangoObjectTypeUtils.get_instance_from_id(info, input['id'], raise_not_found=True)
        elif parent and key:
            attr = getattr(parent, key, None)
            is_single = getattr(attr, "filter", None) is None  # is it a queryset or a single instance?
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
        try:
            return DjangoObjectTypeUtils.get_model_pk(model, global_id)
        except Exception:
            return global_id

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
                        value = [self.db_key(field.queryset.model, v) for v in value]
                    elif isinstance(value, str):
                        value = self.db_key(field.queryset.model, value)

                    self.data[name] = value

        return super().full_clean()

    def clean(self):
        if any(self.errors):
            return

        return super().clean()


class UtilityMutations:

    @classmethod
    def get_form(cls: DjangoModelFormMutation, root, info, **input):
        form = super(UtilityMutations, cls).get_form(root, info, **input)
        setattr(form, 'info', info)
        return form

    @classmethod
    def get_form_kwargs(cls: DjangoModelFormMutation, root, info, **input):
        global_id = input.get('id')
        if global_id:
            model = cls._meta.form_class.Meta.model
            input['id'] = UtilityForm.db_key(model, global_id)

            if not model == get_user_model():
                created_by = model.objects\
                    .filter(pk=input['id'])\
                    .values_list('created_by', flat=True)

                if not created_by:
                    raise ValueError(f'Instance Not Found {global_id}')

                input['created_by'] = created_by[0]
        elif info.context:
            input['created_by'] = info.context.user

        input['last_modified_by'] = info.context.user
        return super(UtilityMutations, cls).get_form_kwargs(root, info, **input)

    def check_errors(self: DjangoModelFormMutation):
        if any(self.errors):
            errors = []
            for e in self.errors:
                if isinstance(e, ErrorType):
                    errors.extend([f'{e.field} - {"".join(e.messages)}'])
                    logger.error(f'Form Error {e.field} - {"".join(e.messages)}', e)
                else:
                    errors.append(str(e))
                    if not isinstance(e, ValidationError):  # log non validation errors
                        logger.error('Form error', e)

            raise GraphQLError('\n'.join(errors))


class UpsertMutation(graphene.Mutation):
    instance = None  # graphene.Field(lambda: DjangoObjectType(cls.Meta.model))

    @classmethod
    def mutate(cls, root, info, input_data):
        instance = UtilityForm.apply_forms(root, info, input_data)
        return cls(instance=instance)


class DeleteMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.ID(description='Global ID')

    @classmethod
    def mutate(cls, root, info, gid):
        obj = DjangoObjectTypeUtils.find_object(gid, raise_not_found=True)
        if callable(getattr(obj, 'delete_check', None)):
            obj.delete_check(info)
        else:
            raise GraphQLError("Object does not support deletion.")

        return cls(ok=True)


class ActivateMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.ID(description='Global ID')
        active = graphene.Boolean(description='Set active or inactive', default_value=True)

    @classmethod
    def mutate(cls, root, info, gid, active=True):
        obj = DjangoObjectTypeUtils.find_object(gid, raise_not_found=True)
        if callable(getattr(obj, 'activate', None)):
            obj.activate(info, active)
        else:
            raise GraphQLError("Object does not support activation.")

        return cls(ok=True)
