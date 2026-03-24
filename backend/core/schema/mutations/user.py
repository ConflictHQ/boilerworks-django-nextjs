import logging
import uuid
from email.headerregistry import Address

import graphene
from core.emails import Emails, WelcomeEmailParameters
from core.models import Profile, SignRequest
from core.schema.mutations.common import UpsertMutation, UtilityForm
from core.schema.mutations.restricted_serializer_mutation import RestrictedSerializerMutation
from core.schema.user import SignRequestType, UserType
from core.serializers.profile import ProfileSerializer
from core.systems import EmailRequest
from django import forms
from django.conf import settings
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from graphene_django.types import ErrorType
from graphql import GraphQLError
from graphql_relay import from_global_id

try:
    from django.contrib.auth import HASH_SESSION_KEY as AUTH_HASH_SESSION_KEY
except ImportError:
    AUTH_HASH_SESSION_KEY = '_auth_user_hash'

logger = logging.getLogger(__name__)


class ProfileForm(UtilityForm, forms.ModelForm):
    class Meta:
        model = Profile
        fields = 'avatar', 'created_by'


class ProfileInput(graphene.InputObjectType):
    avatar = graphene.String(required=False)


class ProfileMutation(RestrictedSerializerMutation):
    # The class attributes define the response of the mutation
    ok = graphene.Boolean()
    errors = graphene.List(ErrorType)

    class Meta:
        serializer_class = ProfileSerializer
        lookup_field = 'gid'
        model_operation = ['create']
        fields = "__all__"

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        fields_provided = input.keys()

        # Get the user who is making the call
        user_id = info.context.user.id

        if 'user' in fields_provided and 'id' in input['user']:
            user_id = from_global_id(input['user']['id']).id
            input['user']['id'] = user_id

        instance = Profile.objects.filter(user_id=user_id).first()

        if 'address' in fields_provided and 'state' in input['address']:
            input['address']['state'] = input['address']['state'].value

        if 'gender' in fields_provided:
            input['gender'] = input['gender'].value

        if 'preferred_contact' in fields_provided:
            input['preferred_contact'] = input['preferred_contact'].value

        if 'preferred_language' in fields_provided:
            input['preferred_language'] = input['preferred_language'].value

        if instance is None:
            return {'data': input, 'partial': True, "context": {"request": info.context}}
        else:
            return {'instance': instance, 'data': input, 'partial': True, "context": {"request": info.context}}

    @classmethod
    def response(cls, ok, errors):
        return ProfileMutation(ok=ok, errors=errors)


class RequestPwdChangeMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        user_gid = graphene.ID(
            description='User ID. Sends the reset password email to this user'
                        'If not provided, the current user will receive the email.'
                        'Requires PROFILE_CHANGE_RESET_PASSWORD_USERS permission '
                        'to send to other users'
        )

    @classmethod
    def mutate(cls, root, info, user_gid=None):
        user = user_gid and UserType.get_object(info, user_gid, raise_not_found=True) or\
               info.context.user

        if user != info.context.user:
            from config.roles_gen import P
            P.PROFILE_CHANGE_RESET_PASSWORD_USERS.check(
                info.context.user, True
            )

        user.profile.request_reset_password()
        return cls(ok=True)


class RequestDeleteUserMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        user_gid = graphene.ID(
            description='User ID. Request to delete user.'
                        'If not provided, the current user will be deleted.'
                        'Requires PROFILE_DELETE_USERS permission if deleting other users'
        )

    @classmethod
    def mutate(cls, root, info, user_gid=None):
        user = user_gid and UserType.get_object(info, user_gid, raise_not_found=True) or\
               info.context.user

        if user != info.context.user:
            from config.roles_gen import P
            P.PROFILE_DELETE_USERS.check(
                info.context.user, True
            )

        Profile.anonymize_user(user)
        if user == info.context.user:
            logout(info.context)

        return cls(ok=True)


class UserForm(UtilityForm, forms.Form):
    id = forms.CharField(max_length=50, required=False)
    username = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    avatar = forms.URLField(required=False)
    phone_number = forms.CharField(max_length=50, required=False)

    created_by = forms.ModelChoiceField(get_user_model().objects, required=False)
    last_modified_by = forms.ModelChoiceField(get_user_model().objects, required=False)

    class Meta:
        model = get_user_model()

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def save(self):
        self.cleaned_data = {k: v for k, v in self.cleaned_data.items() if not v == ''}
        is_new_user = self.instance.profile.is_new_user()
        forms.models.construct_instance(self, self.instance, self.fields)

        profile_original, profile_draft = Profile.objects.get_draft(self.instance.profile)
        profile = profile_draft
        profile.document_option = Profile.DocumentOptions.DRAFTED

        forms.models.construct_instance(self, profile, self.fields)

        self.instance.save()
        profile.save()
        self.cleaned_data['user'] = self.instance

        if is_new_user and not profile_original.is_new_user():
            Emails.WELCOME(
                EmailRequest(
                    subject=f'Welcome {self.first_name} {self.last_name}',
                    recipients=[Address(
                        display_name=f'{self.first_name} {self.last_name}',
                        addr_spec=self.email
                    )]
                ),
                WelcomeEmailParameters(
                    first_name=self.first_name,
                    last_name=self.last_name,
                )
            )

        return self.instance


class UserForm2(UtilityForm, ModelForm):
    class Meta:
        model = get_user_model()
        fields = 'username', 'first_name', 'last_name',

    def save(self, *args, **kwargs):
        # email is not allowed to be changed
        return super().save(*args, **kwargs)

    def post_save(self, data):
        self.instance.save()
        return self.instance


class UserInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    username = graphene.String(required=True)
    first_name = graphene.String(required=False)
    last_name = graphene.String(required=False)
    profile = ProfileInput(required=False)


UtilityForm.register_form(UserInput, UserForm2)


class UpsertUserMutation(UpsertMutation):
    # The class attributes define the response of the mutations
    instance = graphene.Field(UserType)

    class Arguments:
        input_data = UserInput(required=True, name="input")

    @classmethod
    def mutate(cls, root, info, input_data):
        input_data['id'] = UserType.to_global_id(info.context.user)
        return super().mutate(root, info, input_data)

    @classmethod
    def perform_mutate(cls, form, info):
        super().perform_mutate(form, info)
        form.cleaned_data['id'] = UserType.to_global_id(form.cleaned_data['user'])
        return cls(errors=[], **form.cleaned_data)

    def resolve_user(self, info, **kwargs):
        self.check_errors()
        return self.user


class LoginMutationMagic(graphene.Mutation):
    class Arguments:
        did_token = graphene.String(description='Magic did token')

    user = graphene.Field(UserType)

    @classmethod
    def mutate(cls, root, info, did_token):
        user = authenticate(request=info.context, magic_token=did_token)
        is_new_user = not user and 'email' in info.context.session

        if is_new_user:
            email = info.context.session['email']
            gid = uuid.uuid4()
            user = get_user_model().objects.create(username=gid.hex, email=email)
            user.profile = Profile.objects.create(
                gid=gid,
                user=user,
                created_by=get_user_model().objects.get(username=settings.API_SYSTEM_USER)
            )
        elif not user:
            raise PermissionDenied('Invalid Token')

        login(info.context, user)

        if hasattr(info.context, "user"):
            info.context.user = user

        return cls(user=user)


class LoginMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(description='Username')
        password = graphene.String(description='Password')

    user = graphene.Field(UserType)

    @classmethod
    def mutate(cls, root, info, username, password):
        user = authenticate(request=info.context, username=username, password=password)
        if not user:
            raise PermissionDenied('User not found')

        login(info.context, user)

        if hasattr(info.context, "user"):
            info.context.user = user

        return cls(user=user)


class LogoutMutation(graphene.Mutation):
    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info):
        logout(info.context)
        return cls(ok=True)


class SwitchUserMutation(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        id = graphene.ID(description='User ID')

    @classmethod
    def mutate(cls, root, info, id):
        user: User = info.context.user
        if id == '':
            if 'MAIN_USER_PK' not in info.context.session:
                return cls(user=info.context.user)
            other_user = User.objects.get(pk=info.context.session['MAIN_USER_PK'])
        else:
            other_user = UserType.get_object(info, id, raise_not_found=True)

        info.context.user = other_user
        info.context.session[AUTH_SESSION_KEY] = other_user.pk
        info.context.session[AUTH_HASH_SESSION_KEY] = other_user.get_session_auth_hash()

        if 'MAIN_USER_PK' not in info.context.session:
            info.context.session['MAIN_USER_PK'] = user.pk

        info.context.session.save()

        return cls(user=info.context.user)


class PinUpdateMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        pin = graphene.String(description='User Pin')

    @classmethod
    def mutate(cls, root, info, pin):
        user = info.context.user
        user.profile.update_pin(pin)
        return cls(ok=True)


class PinTransactionMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        pin = graphene.String(description='User Pin')
        proxy_user = graphene.ID(description='Proxy User ID. The pin belongs to this user and '
                                             'the current user is acting on behalf of this user. '
                                             'Current user must have the permission to act on behalf of the proxy user.')

    @classmethod
    def mutate(cls, root, info, pin, proxy_user=None, data=None):
        profile: Profile = info.context.user.profile
        if proxy_user:
            proxy_user = UserType.get_object(info, proxy_user, raise_not_found=True)

        profile.authenticate(pin, proxy_user, data)
        return cls(ok=True)


class SignRequestUserMutation(graphene.Mutation):
    """
    This mutation is used to request a sign to a user.
    In order to request a sign:
        * the user must have the permission SIGNREQUEST_CHANGE_SIGN
    """
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.String(description='Global ID of the Sign Request')
        user_to_request = graphene.ID(description='Global User ID to request the sign')

    @classmethod
    def mutate(cls, root, info, gid, user_to_request):
        # SignRequestType.get_object can not be used because of the security in SignRequestType
        # This assume everyone can request a sign
        sign_request_pk = SignRequestType.get_pk(gid)
        sign_request = SignRequest.objects.filter(pk=sign_request_pk).first()

        if not sign_request:
            raise GraphQLError(f'Object id {str(cls)}:{gid} not found')

        user_to_request = UserType.get_object(info, user_to_request, raise_not_found=True)
        if sign_request.is_rejected:
            sign_request = sign_request.reset_sign_request(user_to_request)

        sign_request.request_user(user_to_request)
        return cls(ok=True)


class SignRequestSignMutation(graphene.Mutation):
    """
    This mutation is used to sign a sign request.
    In order to sign a sign request
        * the current user must have:
            * The permission SIGNREQUEST_CHANGE_SIGN
            * Pin transaction active
        * the status the request must be SIGN_REQUIRED
    """
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.String(description='Global ID of the Sign Request')

    @classmethod
    def mutate(cls, root, info, gid):
        sign_request = SignRequestType.get_object(info, gid, raise_not_found=True)
        sign_request.sign(info.context.user)
        return cls(ok=True)


class SignRequestCancelMutation(graphene.Mutation):
    """
    This mutation is used to cancel the SignRequest. This invalidates the whole sign request.
    In order to cancel a sign
        * the current user must have:
            * The permission SIGNREQUEST_CHANGE_CANCEL
    """
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.String(description='Global ID of the Sign Request')
        note = graphene.String(description='Note for the cancellation')

    @classmethod
    def mutate(cls, root, info, gid, note):
        sign_request = SignRequestType.get_object(info, gid)
        sign_request.cancel(info.context.user, note)
        return cls(ok=True)
