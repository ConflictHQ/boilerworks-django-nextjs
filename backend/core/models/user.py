import json
import logging
import re
import unicodedata
import uuid
from datetime import timedelta
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Tuple

from config.roles_gen import P
from constance import config
from core.middleware.current_user import get_current_user
from core.models import GlobalIDLink, RequiresApproveMixin, Tracking
from core.models.address import Address
from core.models.upload import Upload
from core.utils.exceptions import ValidationErrorBuilder
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Model, Q, QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from phonenumber_field.modelfields import PhoneNumberField
from pushnotif.models import DeepLink

logger = logging.getLogger(__name__)


class PinTransactionKindChoices(models.TextChoices):
    """
    Options for the pin transaction
    """
    CHANGED = 'changed', 'Changed'
    AUTHENTICATED = 'authenticated', 'Authenticated'
    FAIL = 'fail', 'Fail'


def get_pin_transaction_valid_time():
    return timezone.now() - timedelta(minutes=30)


class PinTransactionQuerySet(QuerySet):
    def active_authentication(self, user: User) -> 'PinTransaction':
        return self.filter(user=user, sealed=False, kind=PinTransactionKindChoices.AUTHENTICATED,
                           created_at__gte=get_pin_transaction_valid_time()).first()


class PinTransaction(models.Model):
    """
    Log of the pin transactions
    Transaction is valid for 30 minutes
    Transactions UUID must never be received from the client
    """
    objects = PinTransactionQuerySet.as_manager()

    transaction = models.UUIDField(default=uuid.uuid4, editable=False)

    kind = models.CharField(
        max_length=20,
        choices=PinTransactionKindChoices.choices,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False,
        related_name='pin_transactions',
        help_text='User associated with the PIN transaction'
    )

    proxy_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        editable=False,
        related_name='proxy_pin_transactions',
        help_text='User that requested the pin transaction. For example the proxy user is'
                  'using his phone and the user introduce the pin to confirm.'
                  'If null the owner of the pin is the requester'
    )

    sealed = models.BooleanField(
        default=False,
        editable=False,
        help_text='Indicates if the transaction is no longer active.'
    )

    data = models.JSONField(
        null=True,
        blank=True,
        editable=False,
        help_text='Extra data for the transaction'
    )

    created_at_override = models.DateTimeField(null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        permissions = (
            ('add_transaction_using_proxy_user_pin', 'Can add transaction using proxy user pin'),
        )

    def __str__(self):
        return f'{self.user} - {self.created_at}'

    def seal(self):
        self.sealed = True
        self.save()

    def is_sealed(self):
        expired = self.created_at > get_pin_transaction_valid_time()
        if expired:
            self.seal()
        return self.sealed

    @property
    def effective_created_at(self):
        return self.created_at_override if self.created_at_override else self.created_at

    @classmethod
    def add_transaction(cls, user, kind, proxy_user=None, data=None):
        if proxy_user and kind == PinTransactionKindChoices.AUTHENTICATED:
            P.PINTRANSACTION_ADD_TRANSACTION_USING_PROXY_USER_PIN.check(user)

        active = cls.objects.active_authentication(user)
        if active:
            active.seal()

        sealed = kind != PinTransactionKindChoices.AUTHENTICATED
        return cls.objects.create(user=user, kind=kind, proxy_user=proxy_user, sealed=sealed,
                                  data=data)


class SignRequestStatusChoices(models.TextChoices):
    """
    Options for the sign request kind
    """
    IN_PROGRESS = 'in_progress', 'In Progress'  # The process is in progress and is not ready to be signed
    SIGN_REQUIRED = 'sign_required', 'Sign Required'
    CANCELED = 'canceled', 'Canceled'
    SIGNED = 'signed', 'Signed'

    @classmethod
    def active(cls):
        return cls.IN_PROGRESS, cls.SIGN_REQUIRED, cls.SIGNED

    @classmethod
    def signed(cls):
        return cls.SIGNED,


class SignRequestMixin:
    """
    Mixin for the objects that in global_id_link. This allows to use mutations on the core
    and interact with the objects that have sign requests.
    """

    def author_can_sign(self) -> bool:
        """Flag that specifies whether the author or creator of the signRequest can sign it."""
        return False

    def users_allowed_to_sign(self) -> QuerySet[User]:
        """Return the list of users that can sign the request"""
        ...

    def on_request_sign(self, user: User):
        """Allows the related object to raise an error if the user can not request the sign
        return True if the user can request the sign, False otherwise with a reason
        """
        pass

    def on_sign(self, user: User):
        """Allows the related object to raise an error if the user can not sign the request"""
        pass

    def on_cancel(self, user: User):
        """Allows the related object to raise an error if the user can not reject the request"""
        pass

    def on_request_sign_change(self, previous_status: SignRequestStatusChoices,
                               current_status: SignRequestStatusChoices):
        """This called after the sign request status changes"""
        pass

    def on_reset_sign_request(self) -> 'SignRequest':
        """This called after the sign request is reset"""
        pass


@DeepLink.register(
    webapp="/competency-signoff-details/%(global_id)s",
    mobile="boilerworks://app/competency-signoff-details/%(global_id)s",
)
class SignRequest(Tracking):
    """
    Core. SignRequest are used to request signatures from users, with this class we have a way to
    unify the way that we request signs from the users.
    globalIdLink: locate the object that requires the sign.
    When querying, it can be filter by the following action:
        - REQUESTED_BY_ME: Requests created by the current user
        - REQUESTED_OF_ME: Requests to be signed by the current user
        - SIGNED_BY_ME: Requests already signed by the current user
    It can also be filter by using the following statuses:
        - IN_PROGRESS
        - SIGN_REQUIRED
        - CANCELED
        - SIGNED
    The field is mandatory, as it is not permitted to see requests that the current user is not affiliated to.

    TODO: The request can be canceled by the requester.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sign_required',
        help_text='User that requires the sign request.'
    )
    status = models.CharField(max_length=20, choices=SignRequestStatusChoices.choices,
                              default=SignRequestStatusChoices.IN_PROGRESS)
    signs_required = models.IntegerField(default=1, help_text='Number of signs required.',
                                         validators=[MinValueValidator(1)])

    sign_requested = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='sign_requests',
        blank=True,
        help_text='Employees that need to sign this request.'
    )

    signed_by = models.ManyToManyField(
        'core.PinTransaction',
        related_name='competency_logs',
        blank=True,
        help_text='Pin transactions used to sign this log.'
    )

    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='The date when the all the signatures were completed.'
    )

    cancel_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_sign_requests',
        help_text='User that rejected the request.'
    )

    cancel_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='The date when the request was rejected.'
    )

    note = models.TextField(null=True, blank=True, help_text='Note to add details.')

    global_id_link = models.ForeignKey(
        GlobalIDLink,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sign_requests',
        help_text='Global link to the record associated with this sign request.'
    )

    class Meta:
        permissions = (
            ('change_cancel', 'Can cancel the request'),
            ('change_sign', 'Can sign the request'),
            ('view_all', 'Can view the requests of all users'),
        )

    def __str__(self):
        return f'Request: {self.user.last_name} - {self.status}'

    @property
    def is_rejected(self):
        return self.status == SignRequestStatusChoices.CANCELED

    @property
    def is_signed(self):
        return self.status == SignRequestStatusChoices.SIGNED

    def users_allowed_to_sign(self) -> QuerySet[User]:
        instance = self.global_id_link.get_instance()
        if not instance:
            return settings.AUTH_USER_MODEL.objects.none()

        users = instance.users_allowed_to_sign() if isinstance(instance, SignRequestMixin) else self.sign_requested
        query_criteria: Q = Q(groups__permissions__in=[P.SIGNREQUEST_CHANGE_SIGN.perm()])
        if not instance.author_can_sign():
            query_criteria &= ~Q(pk=self.user.id)
        return users.filter(
            query_criteria
        ).distinct()

    def request_user(self, user: User, should_notify: bool = True) -> 'SignRequest':
        """
        Request the sign from the user
        """
        P.SIGNREQUEST_CHANGE_SIGN.check(user)
        self.global_id_link.get_instance().on_request_sign(user)

        (
            ValidationErrorBuilder()
            .check(self.status not in SignRequestStatusChoices.active())
            .validate('sign_request', f'Sign request is not active. It is {self.status}.')
            .check(not self.global_id_link.get_instance().author_can_sign() and user == self.user)
            .validate('sign_request', 'User can not sign his own request.')
            .raise_error()
        )

        self.sign_requested.add(user)
        if should_notify:
            self.notify_signature_request(user)
        return self

    def clear_requests(self):
        self.sign_requested.clear()

    def change_to_sign_required(self):
        self._change_status(SignRequestStatusChoices.SIGN_REQUIRED)

    def change_to_in_progress(self):
        self._change_status(SignRequestStatusChoices.IN_PROGRESS)

    def _change_status(self, status: SignRequestStatusChoices):
        previous_status = self.status
        self.status = status
        self.save()
        self.global_id_link.get_instance().on_request_sign_change(previous_status, status)

    def sign(self, user: User):
        P.SIGNREQUEST_CHANGE_SIGN.check(user)
        self.global_id_link.get_instance().on_sign(user)

        from core.models import PinTransaction
        transaction = PinTransaction.objects.active_authentication(user)

        if user.username == settings.API_SYSTEM_USER:
            logger.info(f'{settings.API_SYSTEM_USER} user is signing request with id {self.global_id}')
        else:
            (
                ValidationErrorBuilder()
                .check(
                    not (
                            self.users_allowed_to_sign().filter(id=user.id).exists()
                            and (
                                self.sign_requested.filter(id=user.id).exists()
                                if self.sign_requested.exists()
                                else True
                            )
                    )
                )
                .validate('user', f'User {user.username} cannot sign this request. It is not in the allowed list.')
                .check(not transaction)
                .validate('user', f'User {user.username} cannot sign this request. There is no active pin transaction.')
                .raise_error()
            )

        self.signed_by.add(transaction)
        if self.signed_by.count() >= self.signs_required:
            self.signed_at = timezone.now()
            self._change_status(SignRequestStatusChoices.SIGNED)

        return self

    def cancel(self, user, note=None):
        P.SIGNREQUEST_CHANGE_CANCEL.check(user)

        self.cancel_by = user
        self.cancel_at = timezone.now()
        self.note = note
        self._change_status(SignRequestStatusChoices.CANCELED)

    def notify_signature_request(self, recipient: User):
        """Send signature request notification (Domain-specific)."""
        try:
            from domain_app.notifications import Notifications, SignRequestParameters
            parameters = SignRequestParameters(sign_request=self, recipient=f'{recipient.first_name} {recipient.last_name}')
            Notifications.SIGNATURES_REQUESTED.send(
                sender=self.user,
                recipient=recipient,
                parameters=parameters,
                instance=self,
            )
        except ImportError:
            # domain app not available - skip notification
            pass

    def reset_sign_request(self, user: User) -> 'SignRequest':
        P.SIGNREQUEST_CHANGE_SIGN.check(user)
        return self.global_id_link.get_instance().on_reset_sign_request()


class UserSwitchGroup(Tracking):
    """
    Users in the same group are allowed to switch between them.
    """
    gid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class ProfileQuerySet(QuerySet):

    def get_by_natural_key(self, user_natural_key):
        return self.get(user=User.objects.get_by_natural_key(user_natural_key))


class PreferredContactOptions(models.TextChoices):
    SMS = 'SMS', 'SMS'
    EMAIL = 'EMAIL', 'Email'
    PHONE = 'PHONE', 'Phone'


class GenderOptions(models.TextChoices):
    FEMALE = 'FEMALE', 'Female'
    MALE = 'MALE', 'Male'
    OTHER = 'OTHER', 'Other'


class ProfileManager(models.Manager.from_queryset(ProfileQuerySet)):

    def draft_address_guard(self, profile: 'Profile', draft: 'Profile'):
        if draft.address_id == profile.address_id:
            if draft.address_id is None:
                return
            #  we need to create a shallow copy of the Address
            draft_address = draft.address
            draft_address.pk = None
            draft_address.save()
            draft.address_id = draft_address.id
            draft.save()
            profile.refresh_from_db()
            draft.refresh_from_db()
            if draft.address_id == profile.address_id:
                raise AssertionError('Unable to create draft address')

    def get_draft(self, profile: 'Profile') -> Tuple['Profile', 'Profile']:
        if profile.parent_id is None:
            draft: Profile = self.filter(parent=profile).first()
            if draft is None:
                profile, draft = self._create_draft(profile)
            self.draft_address_guard(profile, draft)
            return profile, draft
        else:
            self.draft_address_guard(profile.parent, profile)
            return profile.parent, profile

    def _create_draft(self, profile: 'Profile') -> tuple['Profile', 'Profile']:
        parent_gid = profile.gid
        profile.parent_id = parent_gid
        profile.pk = None
        profile.user_id = None
        profile.rocket_id = None
        profile.document_option = Profile.DocumentOptions.DRAFTED
        profile.save()
        original = self.filter(gid=parent_gid).get()
        draft = self.filter(parent_id=parent_gid).get()
        return original, draft

    def promote_draft(self, profile: 'Profile') -> Tuple['Profile', 'Profile']:
        original, draft = self.get_draft(profile)
        draft.document_option = Profile.DocumentOptions.PUBLISHED
        draft_address = draft.address
        draft_address_id = draft.address_id
        profile_address_id = original.address_id
        draft.save()

        match (profile_address_id is None, draft_address_id is None):
            case (False, False):
                draft_address.pk = profile_address_id
                draft_address.save()
            case (False, True):
                logger.warning('This should never happen')
            case (True, False):
                draft_address.pk = None
                draft_address.save()
                profile_address_id = draft_address.id
                draft.address_id = profile_address_id
            case (True, True):
                pass

        parent_gid = original.gid
        draft.pk = original.pk
        draft.parent_id = None
        draft.user_id = original.user_id
        draft.rocket_id = original.rocket_id
        draft.document_option = Profile.DocumentOptions.PUBLISHED
        draft.save()
        original = self.filter(gid=parent_gid).get()
        draft = self.filter(parent_id=parent_gid).get()
        self.update_user(draft)
        return original, draft

    def reject_draft(self, profile: 'Profile') -> Tuple['Profile', 'Profile']:
        original, draft = self.get_draft(profile)
        parent_gid = original.gid
        original.parent_id = original.gid
        original.pk = draft.pk
        original.user_id = None
        original.rocket_id = None
        original.document_option = Profile.DocumentOptions.REJECTED
        original.save()
        original = self.filter(gid=parent_gid).get()
        draft = self.filter(parent_id=parent_gid).get()
        return original, draft

    def update_user(self, profile: 'Profile'):
        user: User = profile.parent.user
        update_user = False
        if (
                profile.first_name != user.first_name or
                profile.last_name != user.last_name
        ):
            update_user = True
        if update_user:
            from core.utils.api.rocketchat_rest_client import RocketchatRestClient
            user.first_name = profile.first_name
            user.last_name = profile.last_name
            user.save()
            client = RocketchatRestClient()
            client.update_user(user)


class Profile(RequiresApproveMixin, Tracking):
    class ImageField(Enum):
        AVATAR = 'avatar'
        SIGNATURE = 'signature'

    class DocumentOptions(models.IntegerChoices):
        PUBLISHED = 0
        DRAFTED = 1
        REJECTED = 2

    objects = ProfileManager()

    gid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document_option = models.IntegerField(
        choices=DocumentOptions,
        default=DocumentOptions.PUBLISHED
    )

    parent = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        unique=True,
        related_name='draft'
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    switch_group = models.ForeignKey(
        UserSwitchGroup,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='profiles',
        help_text='Group of users that can switch between them'
    )

    avatar = models.ForeignKey(
        Upload,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avatar_profiles'
    )

    signature = models.ForeignKey(
        Upload,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signature_profiles'
    )

    rocket_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    active_organization = models.ForeignKey(
        'organization.Organization',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='active_users',
        help_text='Organization that the user is currently logged in'
    )

    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    display_name = models.CharField(max_length=100, null=True, blank=True)
    name_suffix = models.CharField(max_length=50, null=True, blank=True)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=GenderOptions.choices,
        blank=True
    )

    address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        help_text='User address'
    )

    phone_number = PhoneNumberField(null=True, blank=True, unique=False)

    preferred_contact = models.CharField(
        max_length=10,
        choices=PreferredContactOptions.choices,
        blank=True
    )

    preferred_language = models.CharField(
        max_length=2,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE
    )

    pin = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        editable=True
    )

    pin_salt = models.UUIDField(default=uuid.uuid4, editable=False)

    search = models.TextField(null=True, blank=True, editable=False, db_index=True,
                              help_text='Search field for user profile')

    username = models.CharField(
        "username",
        max_length=150,
        default=None,
        blank=True,
        null=True,
        help_text=(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )

    class Meta:
        permissions = (
            # User fields
            ('view_email', 'Can view email field'),
            ('change_email', 'Can change email field'),
            ('view_first_name', 'Can view first_name field'),
            ('change_first_name', 'Can change first_name field'),
            ('view_last_name', 'Can view last_name field'),
            ('change_last_name', 'Can change last_name field'),
            # Profile fields
            ('view_avatar', 'Can view avatar field'),
            ('change_avatar', 'Can change avatar field'),
            ('view_signature', 'Can view signature field'),
            ('change_signature', 'Can change signature field'),
            ('view_middle_name', 'Can view middle_name field'),
            ('change_middle_name', 'Can change middle_name field'),
            ('view_display_name', 'Can view display_name field'),
            ('change_display_name', 'Can change display_name field'),
            ('view_name_suffix', 'Can view name_suffix field'),
            ('change_name_suffix', 'Can change name_suffix field'),
            ('view_nickname', 'Can view nickname field'),
            ('change_nickname', 'Can change nickname field'),
            ('view_birth_date', 'Can view birth_date field'),
            ('change_birth_date', 'Can change birth_date field'),
            ('view_gender', 'Can view gender field'),
            ('change_gender', 'Can change gender field'),
            ('view_address', 'Can view address field'),
            ('change_address', 'Can change address field'),
            ('view_phone_number', 'Can view phone_number field'),
            ('change_phone_number', 'Can change phone_number field'),
            ('view_preferred_contact', 'Can view preferred_contact field'),
            ('change_preferred_contact', 'Can change preferred_contact field'),
            ('change_reset_password_users', 'Can reset password of other users'),
            ('delete_users', 'Can delete users'),
            ('approve_profile_changes', 'Can approve profile changes'),
        )

        constraints = [
            models.UniqueConstraint(fields=['user', 'document_option'], name='user_document_option'),
        ]

    def promote(self) -> None:
        Profile.objects.promote_draft(self)

    def reject(self) -> None:
        Profile.objects.reject_draft(self)

    def save(self, *args, **kwargs):
        if self.parent_id is None:
            if not self.active_organization:
                self.active_organization = self.organization()
            # if a new field is added create a data migration to update the search field
            self.update_search()
            return super().save(*args, **kwargs)
        else:
            return super().save(*args, **kwargs)

    def update_pin(self, pin):
        self.pin = make_password(pin, salt=self.pin_salt.hex)
        self.save()
        PinTransaction.add_transaction(user=self.user, kind=PinTransactionKindChoices.CHANGED)

    def has_pin(self):
        return bool(self.pin)

    def authenticate(self, pin, proxy_user=None, data=None) -> PinTransaction:
        user = proxy_user or self.user
        if not user.profile.has_pin():
            raise ValueError('Pin not set')

        pin_hex = make_password(pin, salt=user.profile.pin_salt.hex)
        if user.profile.pin == pin_hex:
            transaction = PinTransaction.add_transaction(
                user=self.user,
                kind=PinTransactionKindChoices.AUTHENTICATED,
                proxy_user=proxy_user,
                data=data
            )
            return transaction
        PinTransaction.add_transaction(
            user=self.user,
            kind=PinTransactionKindChoices.FAIL,
            proxy_user=proxy_user,
            data=data
        )
        raise ValueError('Invalid pin')

    def update_search(self):
        email = ''
        username = ''
        if self.user:
            email = self.user.email
            username = self.user.username
        fields = {
            username,
            email,
            self.first_name,
            self.last_name,
            self.middle_name,
            self.display_name,
            self.nickname,
            str(self.phone_number or '')
        }
        fields = {str(field).lower() for field in fields}
        self.search = ' '.join([str(field) for field in fields if field])

    def organization(self):
        if not self.active_organization:
            if self.user and self.user.memberships.exists():
                self.active_organization = self.user.memberships.first().organization
            else:
                logger.warning(f'{self.user} is not member of any organization!')
        return self.active_organization

    def active_membership(self):
        return self.user.memberships.filter(organization=self.organization()).first()

    def is_new_user(self):
        return self.gid.hex == self.user.username

    def __str__(self):
        return self.display_name if self.display_name else self.user.__str__()

    def __repr__(self):
        return f'<{self.document_option} Profile {str(self)}>'

    def natural_key(self):
        return self.user.natural_key()

    @staticmethod
    def is_valid_username(username: str) -> bool:
        """
        Validates that a username:
        - starts with at least 4 letters
        - followed by zero or more digits
        """
        pattern = r'^[a-zA-Z]{4,}[0-9]*$'
        return bool(re.match(pattern, username))

    @staticmethod
    def clean_username_fragment(text: str) -> str:
        """
        Removes all characters that are not letters or digits from the username.
        Keeps only a-z, A-Z, and 0-9.
        """
        normalized = unicodedata.normalize("NFD", text)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return re.sub(r'[^a-zA-Z0-9]', '', normalized).strip()

    @classmethod
    def generate_username(cls, first_name: str = '', middle_name: str = '', last_name: str = '') -> str:
        username = ''
        if first_name:
            username += Profile.clean_username_fragment(first_name.capitalize())
        if middle_name:
            username += Profile.clean_username_fragment(middle_name[0]).upper()
        if last_name:
            username += Profile.clean_username_fragment(last_name).capitalize()
        latest_by_prefix: str = User.objects.filter(
            username__istartswith=username,
            first_name__iexact=first_name,
            last_name__iexact=last_name,
        ).order_by('-username').values_list('username', flat=True).first()
        if not latest_by_prefix:
            return username
        latest_by_prefix = latest_by_prefix.replace(username, '')
        numeral = '01'
        if latest_by_prefix:
            numeral = (
                '0' + str(int(latest_by_prefix) + 1)
                if int(latest_by_prefix) < 10
                else str(int(latest_by_prefix) + 1)
            )
        username += numeral
        return username

    @staticmethod
    def add_profile(sender, instance, **kwargs):
        if not hasattr(instance, 'profile'):
            instance.profile = Profile.objects.create(user=instance, username=instance.username)
            if config.AUTH0_REGISTER_NEW_USER:
                instance.profile.register_in_auth0()

    @cached_property
    def active_memberships(self):
        return self.organization().members.filter(member=self.user).first()

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

    def register_in_auth0(self, reset_password=True):
        """
        Register the user profile in the Auth0
        """
        from auth1.sessions import AuthClient
        client = AuthClient.from_settings()

        client.create_auth0_user(
            email=self.user.email,
            phone_number=str(self.phone_number),
        )

        if reset_password:
            client.request_reset_password(self.user.email)

    def request_reset_password(self):
        """
        Request a reset password email
        """
        self.register_in_auth0()

    def anonymize(self, short_uuid=None):
        """
        Request the deletion of the user
        """
        short_uuid = short_uuid or f'anon-{self.id}-{str(uuid.uuid4())[:8]}'

        profile = self
        # Nullifying or replacing PII
        profile.first_name = ""
        profile.last_name = ""
        profile.middle_name = ""
        profile.display_name = short_uuid
        profile.name_suffix = ""
        profile.nickname = short_uuid
        profile.birth_date = None
        profile.gender = ""  # Blank since it's a choice field
        profile.phone_number = None
        profile.preferred_contact = ""
        profile.pin = None
        profile.search = ""

        # Nullify related fields (foreign keys)
        if profile.address:
            profile.address.delete()
        profile.address = None
        if profile.avatar:
            profile.avatar.delete()
        profile.avatar = None
        if profile.signature:
            profile.signature.delete()
        profile.signature = None
        profile.active_organization = None
        profile.switch_group = None
        profile.save()

        match self.document_option:
            case Profile.DocumentOptions.PUBLISHED if self.draft is not None:
                self.draft.anonymize(profile.nickname)

    @classmethod
    @transaction.atomic
    def anonymize_user(cls, user):
        short_uuid = f'anon-{user.id}-{str(uuid.uuid4())[:8]}'
        user.username = short_uuid
        user.first_name = short_uuid
        user.last_name = short_uuid
        user.email = f"{short_uuid}@anon-boilerworks.net"
        user.set_unusable_password()
        user.is_active = False
        user.groups.clear()
        user.save()

        if user.profile:
            user.profile.anonymize(short_uuid)


def system_user(user_model: Optional[type[Model]] = None) -> User:
    user_model = user_model or User
    user, created = user_model.objects.get_or_create(
        username=settings.API_SYSTEM_USER,
        defaults=dict(
            email='noreply@boilerworks.dev',
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
    )
    if created:
        logger.warning(f'User {user.username} was created.')
    return user


class UserStatus(models.TextChoices):
    #  To be use wherever we must filter based on the user's current status (activated, deactivated)
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    ALL = 'ALL'

    def to_db_value(self) -> bool | None:
        if self == UserStatus.ACTIVE:
            return True
        if self == UserStatus.INACTIVE:
            return False
        return None


post_save.connect(Profile.add_profile, sender=User)


@receiver(post_save, sender=Profile, dispatch_uid="profile_edit_timeline")
def create_profile_edit_timeline_entry(sender, instance, created, **kwargs):
    """
    Create timeline entry when a user edits their profile (Domain-specific).
    """
    from core.models import Profile

    # Optional domain app functionality
    try:
        from domain_app.models.employee_timeline import EmployeeTimelineEntry, TimelineEventType, TimelineNoticeType, TimelinePriority
    except ImportError:
        # domain app not available - skip timeline entry
        return

    if not instance.parent or not instance.parent.active_membership():
        return
    employee = instance.parent.active_membership().employee

    current_user = get_current_user()
    if not current_user or not current_user.profile.active_membership():
        return
    responsible_employee = current_user.profile.active_membership().employee

    if instance.document_option == Profile.DocumentOptions.DRAFTED:
        updated_fields = []
        updated_field_values = {}

        if instance.parent:
            fields_to_check = [
                'first_name', 'last_name', 'middle_name', 'display_name',
                'name_suffix', 'nickname',
                'phone_number', 'preferred_contact',
                'birth_date', 'gender', 'preferred_language',
            ]

            for field_name in fields_to_check:
                parent_value = getattr(instance.parent, field_name, None)
                draft_value = getattr(instance, field_name, None)

                try:
                    draft_normalized = json.dumps(draft_value, cls=DjangoJSONEncoder,
                                                  sort_keys=True) if draft_value else None
                    parent_normalized = json.dumps(parent_value, cls=DjangoJSONEncoder,
                                                   sort_keys=True) if parent_value else None
                except Exception:
                    parent_normalized = json.dumps(str(parent_value), cls=DjangoJSONEncoder,
                                                   sort_keys=True) if parent_value else None
                    draft_normalized = json.dumps(str(draft_value), cls=DjangoJSONEncoder,
                                                  sort_keys=True) if draft_value else None

                if parent_normalized != draft_normalized:
                    updated_fields.append(field_name)
                    updated_field_values[field_name] = {
                        'old': json.loads(parent_normalized) if parent_value and parent_normalized else None,
                        'new': json.loads(draft_normalized) if draft_value and draft_normalized else None
                    }

        metadata = {
            'parent_profile_id': str(instance.parent.gid) if instance.parent else None,
            'updated_fields': updated_fields,
            'updated_field_values': updated_field_values,
        }

        if created:
            notice_type = TimelineNoticeType.CREATED_PROFILE_DRAFT
        else:
            notice_type = TimelineNoticeType.UPDATED_PROFILE_DRAFT

        if updated_fields:
            EmployeeTimelineEntry.objects.create(
                employee=employee,
                event_type=TimelineEventType.PROFILE_UPDATE,
                notice_type=notice_type,
                metadata=metadata,
                priority=TimelinePriority.NORMAL,
                related_action_type=instance.__class__.__name__,
                related_action_id=str(instance.gid),
                responsible_employee=responsible_employee,
            )

    elif instance.document_option == Profile.DocumentOptions.PUBLISHED:

        EmployeeTimelineEntry.objects.create(
            employee=employee,
            event_type=TimelineEventType.PROFILE_UPDATE,
            notice_type=TimelineNoticeType.PUBLISHED_PROFILE_DRAFT,
            metadata={},
            priority=TimelinePriority.NORMAL,
            related_action_type=instance.__class__.__name__,
            related_action_id=str(instance.gid),
            responsible_employee=responsible_employee,
        )
