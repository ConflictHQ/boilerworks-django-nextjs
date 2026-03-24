import abc
import types

import graphene
from core.schema import DjangoObjectTypeUtils
from core.utils.graphene_utils import GrapheneUtils
from django.contrib.auth.models import User
from graphene_django.rest_framework.mutation import SerializerMutation
from graphene_django.types import ErrorType


class RestrictedMutationMetaMixin(type(SerializerMutation), abc.ABCMeta):
    ...


class RestrictedSerializerMutation(SerializerMutation, abc.ABC, metaclass=RestrictedMutationMetaMixin):
    ok = graphene.Boolean()
    errors = graphene.List(ErrorType)

    class Meta:
        abstract = True

    @classmethod
    def has_model_permissions(cls, model, user, instance_id=None):
        if instance_id:
            model.p('model').change.check(user)
        else:
            model.p('model').add.check(user)

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        id = input.pop('id', None)
        if id:
            if id and not (isinstance(id, int) or id.isdigit()):
                input['id'] = DjangoObjectTypeUtils.get_pk(id, check_model_name=False)
        return super().get_serializer_kwargs(root, info, **input)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        cls.has_model_permissions(cls._meta.model_class, info.context.user, id)
        kwargs = cls.get_serializer_kwargs(root, info, **input)
        serializer = cls._meta.serializer_class(**kwargs)

        if serializer.is_valid():
            data = cls.perform_mutate(serializer, info)
            data.ok = True
            if hasattr(serializer.instance, 'global_id'):
                data.id = (
                    serializer.instance.global_id()
                    if isinstance(serializer.instance.global_id, types.MethodType)
                    else serializer.instance.global_id
                )
            data.errors = ()
            return data
            # return cls.response(ok=True, errors=())
        else:
            errors = GrapheneUtils.unpack_nested_errors(serializer.errors)
            return cls.response(ok=False, errors=errors, )

    @classmethod
    def delete(cls, device_token: str, user: User) -> bool:
        raise NotImplementedError("Implement method to delete objects via primary key, for globalId use deleteMutation")

    @classmethod
    def response(cls, ok, errors):
        return cls(ok=ok, errors=errors)
