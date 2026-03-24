import logging
from collections import defaultdict
from typing import Iterable

import django_filters
import graphene
import graphene_django_optimizer as gql_optimizer
from config.roles_gen import P
from constance import config
from core.dataloaders import DataLoaderContext, dataloader
from core.models import PinTransaction, Profile, SignRequest, SignRequestStatusChoices, UserSwitchGroup
from core.schema import CoreProfileDocumentOptionChoices
from core.schema.common import DjangoObjectTypeUtils, MetaNode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, QuerySet
from django_filters import OrderingFilter

# Optional imports - Domain-specific functionality
try:
    from domain_app.models import CompetencyRecord, CompetencyRecordLog, DepartmentEmployee, Employee
    from domain_app.models.forms import FormCategoryChoices
    HAS_DOMAIN_APP = True
except ImportError:
    CompetencyRecord = None
    CompetencyRecordLog = None
    DepartmentEmployee = None
    Employee = None
    FormCategoryChoices = None
    HAS_DOMAIN_APP = False

try:
    from domain_search.documents import ProfileDocument
    HAS_DOMAIN_SEARCH = True
except ImportError:
    ProfileDocument = None
    HAS_DOMAIN_SEARCH = False

from graphene_django import DjangoConnectionField, DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter
from organization.models import OrganizationMember
from pydash import snake_case

logger = logging.getLogger(__name__)


class PinTransactionFilter(django_filters.FilterSet):
    order_by = OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('user__username', 'user_username'),
            ('kind', 'kind'),
        ),
        field_labels={
            'created_at': 'Creation date',
            'updated_at': 'Update date',
            'user_username': 'User',
            'kind': 'Kind',
        },
        method='filter_order_by',
    )

    class Meta:
        model = PinTransaction
        fields = ['kind', 'user', 'sealed']

    def filter_order_by(self, queryset, name, value):
        from django.db.models.functions import Coalesce

        if not value:
            return queryset

        ordering = []
        for field in value:
            if field == 'created_at':
                queryset = queryset.annotate(
                    _order_created_at=Coalesce('created_at_override', 'created_at')
                )
                ordering.append('_order_created_at')
            elif field == '-created_at':
                queryset = queryset.annotate(
                    _order_created_at=Coalesce('created_at_override', 'created_at')
                )
                ordering.append('-_order_created_at')
            else:
                ordering.append(field)

        return queryset.order_by(*ordering) if ordering else queryset


class PinTransactionType(DjangoObjectType, DjangoObjectTypeUtils):
    created_at = graphene.DateTime(
        description='The effective creation timestamp. Returns created_at_override if set, otherwise created_at.'
    )

    class Meta(MetaNode):
        model = PinTransaction
        filterset_class = PinTransactionFilter

    @staticmethod
    def resolve_created_at(root: PinTransaction, info):
        return root.effective_created_at


object_type_choices = {
    # Domain-specific mappings (only available when domain app is installed)
    **(
        {
            snake_case(CompetencyRecord.__name__).upper(): CompetencyRecord.__name__,
            snake_case(CompetencyRecordLog.__name__).upper(): CompetencyRecordLog.__name__,
            FormCategoryChoices.DISCIPLINARY.name: FormCategoryChoices.DISCIPLINARY.value,
        }
        if HAS_DOMAIN_APP
        else {}
    ),
}


class SignRequestFilter(django_filters.FilterSet):
    action = django_filters.MultipleChoiceFilter(
        method='_filter_by_action',
        choices=[
            ('REQUESTED_BY_ME', 'Requested by me'),
            ('REQUESTED_OF_ME', 'Requested of me'),
            ('SIGNED_BY_ME', 'Signed by me'),
            ('ALL', 'All'),
        ],
        required=True,
    )
    object_type = django_filters.MultipleChoiceFilter(
        method='_filter_by_object_type',
        choices=object_type_choices,
        required=False,
    )
    id = GlobalIDFilter(method='_filter_by_id')
    status = django_filters.ChoiceFilter(choices=SignRequestStatusChoices.choices)
    ordering = OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('user__first_name', 'user_firstname'),
            ('user__last_name', 'user_lastname'),
            ('user__username', 'user_username'),
            ('updated_at', 'updated_at'),
            ('status', 'status'),
        ),
        field_labels={
            'created_at': 'Creation date',
            'user_firstname': 'User first name',
            'user_lastname': 'User last name',
            'user_username': 'Username',
            'updated_at': 'Update date',
            'status': 'Status',
        },
    )
    user = django_filters.CharFilter(method='_filter_by_user')

    class Meta:
        model = SignRequest
        fields = {
            'created_at': ['gte', 'lte'],
            'status': ['iexact'],
        }

    def __init__(self, data=None, *args, **kwargs):
        if data is not None and 'status' in data:
            raw_value = data.get('status')
            if raw_value:
                valid_map = {
                    str(k).lower(): k
                    for k, _ in self.base_filters['status'].extra['choices']
                }
                normalized = valid_map.get(str(raw_value).lower())
                if normalized:
                    data = data.copy()
                    data['status'] = normalized
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        base_qs: QuerySet[SignRequest] = super().qs
        return base_qs.annotate(sign_requested_count=Count('sign_requested')).filter(sign_requested_count__gt=0)

    def _filter_by_action(self, queryset: QuerySet[SignRequest], name, value):
        user = self.request.user
        filters: Q = Q()
        exclude_other_users: bool = True
        if 'ALL' in value:
            P.SIGNREQUEST_VIEW_ALL.check(user)
            return queryset.filter()
        if 'REQUESTED_OF_ME' in value:
            compound_filter = Q(sign_requested__in=[user])
            compound_filter.add(~Q(signed_by__user__in=[user]), Q.AND)
            filters = filters.add(compound_filter, Q.OR)
            exclude_other_users = False
        if 'SIGNED_BY_ME' in value:
            filters = filters | Q(signed_by__user__in=[user])
            exclude_other_users = False
        if 'REQUESTED_BY_ME' in value or exclude_other_users:
            filters = filters | Q(user=user)
        return queryset.filter(filters).distinct()

    def _filter_by_id(self, queryset, name, value):
        if value:
            return queryset.filter(id=SignRequestType.get_pk(value))
        return queryset

    def _filter_by_object_type(self, queryset: QuerySet[SignRequest], name, value):
        if value and len(value) > 0:
            search_types = [object_type_choices.get(k) for k in value]
            return queryset.filter(global_id_link__type__in=search_types)
        return queryset.filter()

    def _filter_by_user(self, queryset, name, value):
        return queryset.filter(user__profile__search__icontains=value)


class SignRequestType(DjangoObjectType, DjangoObjectTypeUtils):

    users_allowed_to_sign = DjangoFilterConnectionField('core.schema.user.UserType',
                                                        description='Users with the permission to sign the request '
                                                                    'If the user is already in the request list it '
                                                                    'will not be included')

    class Meta(MetaNode):
        model = SignRequest
        filterset_class = SignRequestFilter

    @staticmethod
    def resolve_users_allowed_to_sign(root, info, **kwargs):
        return root.users_allowed_to_sign()


SignRequestType.__doc__ = SignRequest.__doc__


class ActiveType(graphene.ObjectType):
    organization = graphene.Field('organization.schema.OrganizationType')
    membership = graphene.Field('organization.schema.OrganizationMemberType')
    if HAS_DOMAIN_APP:
        department_employees = graphene.List(
            'domain_app.schema.DepartmentEmployeeType',
            description="Deprecated in favor of department_employee, which allows for filtering."
        )
        department_employee = DjangoFilterConnectionField('domain_app.schema.DepartmentEmployeeType')


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr='icontains', field_name='email')
    first_name = django_filters.CharFilter(lookup_expr='icontains', field_name='first_name')
    last_name = django_filters.CharFilter(lookup_expr='icontains', field_name='last_name')
    search = django_filters.CharFilter(method='_filter_by_search')
    username = django_filters.CharFilter(lookup_expr='icontains', field_name='username')

    class Meta:
        model = get_user_model()
        fields = ['email', 'first_name', 'last_name', 'search', 'username']

    def _filter_by_search(self, queryset, name, value):
        if config.SEARCH_PROFILE_ENABLED and HAS_DOMAIN_SEARCH:
            logger.info("Using opensearch for profile search")
            profile_search = ProfileDocument.search().query({"multi_match": {"query": value, "fields": ['*']}})
            ids = [hit.user.id for hit in profile_search if hit.user.id is not None]
            logger.info("Found %s users", str(ids))
            return queryset.filter(id__in=ids)
        else:
            logger.info("Using search field for profile search")
            return queryset.filter(profile__search__icontains=value)


class UserType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = get_user_model()
        exclude = 'password',
        filterset_class = UserFilter

    is_anonymous = graphene.Boolean(source='is_anonymous')
    is_new_user = graphene.Boolean()
    active = graphene.Field(ActiveType)
    memberships = DjangoConnectionField('organization.schema.OrganizationMemberType')
    email = graphene.String()
    employee_id = graphene.String()
    username = graphene.String(
        description='Active username, edits are queued for approval via ProfileType.username'
    )

    @classmethod
    def get_queryset(cls, queryset, info):
        return gql_optimizer.query(queryset, info)

    @staticmethod
    def resolve_is_new_user(root, info):
        return root.profile.is_new_user()

    @staticmethod
    @dataloader
    def load_active_by_user_id(context: DataLoaderContext, user_ids: list[int]):
        from organization.schema import Organization, OrganizationCache

        organization_cache = OrganizationCache(context)

        memberships: dict[int, OrganizationMember] = {
            membership.member_id: membership
            for membership in
            OrganizationMember.objects.filter(member_id__in=user_ids, organization=context.organization)
            if membership.is_active
        }

        membership_ids = [membership.id for membership in memberships.values()]

        organizations: dict[int, Organization] = {
            membership.member_id: organization_cache[membership.organization_id]
            for membership in memberships.values()
        }

        if not HAS_DOMAIN_APP:
            # Domain-specific functionality not available
            return []

        department_employees: defaultdict[int, list[DepartmentEmployee]] = defaultdict(list)
        department_employees_queryset: Iterable[DepartmentEmployee] = DepartmentEmployee.objects.filter(
            employee__membership__id__in=membership_ids,
        ).annotate(
            user_id=F('employee__membership__member__id')
        ).prefetch_related('employee')

        for department_employee in department_employees_queryset:
            department_employees[department_employee.user_id].append(department_employee)

        for user_id in user_ids:
            yield user_id, ActiveType(
                organization=organizations.get(user_id, None),
                membership=memberships.get(user_id, None),
                department_employees=department_employees.get(user_id, [])
            )

    @staticmethod
    def resolve_active(root, info):
        return info.context.load_active_by_user_id(root.id)

    @staticmethod
    def resolve_memberships(root: User, info, active_organization=False):
        user = root
        main_user_pk = info.context.session.get('main_user_pk', user.pk)
        if main_user_pk != user.pk:
            user = get_user_model().objects.filter(pk=main_user_pk).first()

        if active_organization:
            return user.memberships.filter(is_active=True)

        return user.memberships

    @staticmethod
    def resolve_meta(root: User, info):
        return root

    @staticmethod
    def resolve_email(root: User, info):
        return root.email

    @staticmethod
    def resolve_profile(root: User, info):
        return info.context.load_profile_from_user_ids(root.id)

    @dataloader
    @staticmethod
    def load_profile_first_name_from_user_ids(_context: DataLoaderContext, user_ids):
        """
        DataLoader for user profiles.
        """
        first_name_by_user_id = {key: '' for key in user_ids}

        for user in get_user_model().objects.filter(id__in=user_ids):
            key = user.id
            first_name_by_user_id[key] = user.first_name or first_name_by_user_id[key]

        for profile in Profile.objects.filter(user_id__in=user_ids):
            key = profile.user_id
            first_name_by_user_id[key] = profile.first_name or first_name_by_user_id[key]

        for key, value in first_name_by_user_id.items():
            yield key, value

    @staticmethod
    def resolve_first_name(root: User, info):
        if info.context.check_permission(
                f"Profile.p('first_name').view.by({info.context.user.id})",
                lambda: Profile.p('first_name').view.by(info.context.user)
        ):
            return info.context.load_profile_first_name_from_user_ids(root.id)
        return ''

    @dataloader
    @staticmethod
    def load_profile_last_name_from_user_ids(_context: DataLoaderContext, user_ids):
        """
        DataLoader for user profiles.
        """
        last_name_by_user_id = {key: '' for key in user_ids}

        for user in get_user_model().objects.filter(id__in=user_ids):
            key = user.id
            last_name_by_user_id[key] = user.last_name or last_name_by_user_id[key]

        for profile in Profile.objects.filter(user_id__in=user_ids):
            key = profile.user_id
            last_name_by_user_id[key] = profile.last_name or last_name_by_user_id[key]

        for key, value in last_name_by_user_id.items():
            yield key, value

    @staticmethod
    def resolve_last_name(root: User, info):
        if info.context.check_permission(
                f"Profile.p('first_name').view.by({info.context.user.id})",
                lambda: Profile.p('first_name').view.by(info.context.user)
        ):
            return info.context.load_profile_last_name_from_user_ids(root.id)
        return ''

    @staticmethod
    def resolve_employee_id(root: User, info):
        if root.username == settings.API_SYSTEM_USER:
            return None
        if not HAS_DOMAIN_APP:
            return None
        employee = Employee.objects.first_user(root)
        return employee.global_id() if employee else None


class UserSwitchType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = UserSwitchGroup


class ProfileType(DjangoObjectType, DjangoObjectTypeUtils):
    email = graphene.String(description='Direct reference to User.email.')
    first_name = graphene.String(description='Direct reference to User.first_name.')
    last_name = graphene.String(description='Direct reference to User.last_name.')
    username = graphene.String(
        description='When Published, works as a direct reference to User.username.'
                    ' Allows for username edits to be queued for approval'
    )
    has_pin = graphene.Boolean()
    document_option = graphene.Field(CoreProfileDocumentOptionChoices)

    class Meta(MetaNode):
        model = Profile
        exclude = ('pin', 'pin_salt', 'search',)

    @staticmethod
    def resolve_email(root: Profile, info):
        if Profile.p('email').view.by(info.context.user):
            return root.user.email
        return None

    @staticmethod
    def resolve_first_name(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('first_name').view.by({info.context.user.id})",
                lambda: Profile.p('first_name').view.by(info.context.user)
        ):
            return root.first_name
        return None

    @staticmethod
    def resolve_last_name(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('last_name').view.by({info.context.user.id})",
                lambda: Profile.p('last_name').view.by(info.context.user)
        ):
            return root.last_name
        return None

    @staticmethod
    def resolve_is_us_citizen(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('is_us_citizen').view.by({info.context.user.id})",
                lambda: Profile.p('is_us_citizen').view.by(info.context.user)
        ):
            return root.is_us_citizen
        return None

    @dataloader
    @staticmethod
    def load_upload_by_id(context: DataLoaderContext, upload_ids: list[int], **kwargs):
        from core.models import Upload
        for upload in Upload.objects.filter(id__in=upload_ids):
            yield upload.id, upload

    @staticmethod
    def resolve_avatar(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('avatar').view.by({info.context.user.id})",
                lambda: Profile.p('avatar').view.by(info.context.user)
        ):
            return info.context.load_upload_by_id(root.avatar_id)
        return None

    @staticmethod
    def resolve_signature(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('signature').view.by({info.context.user.id})",
                lambda: Profile.p('signature').view.by(info.context.user)
        ):
            return info.context.load_upload_by_id(root.signature_id)
        return None

    @staticmethod
    def resolve_middle_name(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('middle_name').view.by({info.context.user.id})",
                lambda: Profile.p('middle_name').view.by(info.context.user)
        ):
            return root.middle_name
        return None

    @staticmethod
    def resolve_display_name(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('display_name').view.by({info.context.user.id})",
                lambda: Profile.p('display_name').view.by(info.context.user)
        ):
            return root.display_name
        return None

    @staticmethod
    def resolve_name_suffix(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('name_suffix').view.by({info.context.user.id})",
                lambda: Profile.p('name_suffix').view.by(info.context.user)
        ):
            return root.name_suffix
        return None

    @staticmethod
    def resolve_nickname(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('nickname').view.by({info.context.user.id})",
                lambda: Profile.p('nickname').view.by(info.context.user)
        ):
            return root.nickname
        return None

    @staticmethod
    def resolve_birth_date(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('birth_date').view.by({info.context.user.id})",
                lambda: Profile.p('birth_date').view.by(info.context.user)
        ):
            return root.birth_date
        return None

    @staticmethod
    def resolve_gender(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('gender').view.by({info.context.user.id})",
                lambda: Profile.p('gender').view.by(info.context.user)
        ):
            return root.gender
        return ""

    @staticmethod
    def resolve_address(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('address').view.by({info.context.user.id})",
                lambda: Profile.p('address').view.by(info.context.user)
        ):
            return root.address
        return None

    @staticmethod
    def resolve_phone_number(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('phone_number').view.by({info.context.user.id})",
                lambda: Profile.p('phone_number').view.by(info.context.user)
        ):
            return root.phone_number
        return None

    @staticmethod
    def resolve_emergency_phone_number(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('emergency_phone_number').view.by({info.context.user.id})",
                lambda: Profile.p('emergency_phone_number').view.by(info.context.user)
        ):
            return root.emergency_phone_number
        return None

    @staticmethod
    def resolve_emergency_contact_name(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('emergency_contact_name').view.by({info.context.user.id})",
                lambda: Profile.p('emergency_contact_name').view.by(info.context.user)
        ):
            return root.emergency_contact_name
        return None

    @staticmethod
    def resolve_emergency_contact_relationship(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('emergency_contact_relationship').view.by({info.context.user.id})",
                lambda: Profile.p('emergency_contact_relationship').view.by(info.context.user)
        ):
            return root.emergency_contact_relationship
        return None

    @staticmethod
    def resolve_preferred_contact(root: Profile, info):
        if info.context.check_permission(
                f"Profile.p('preferred_contact').view.by({info.context.user.id})",
                lambda: Profile.p('preferred_contact').view.by(info.context.user)
        ):
            return root.preferred_contact
        return None

    @staticmethod
    def resolve_has_pin(root: Profile, info):
        return root.has_pin()

    @staticmethod
    def resolve_document_option(root: Profile, info):
        return CoreProfileDocumentOptionChoices.get(root.document_option)


class UserQuery(graphene.ObjectType):
    users = DjangoFilterConnectionField(UserType)
    user = graphene.Field(UserType, id=graphene.ID())
    me = graphene.Field(UserType)
    sign_requests = DjangoFilterConnectionField(SignRequestType, description=SignRequest.__doc__)

    @staticmethod
    def resolve_user(root, info, id, **kwargs):
        if info.context.user.is_anonymous:
            raise PermissionDenied('Not Allowed')

        return UserType.get_object(info, id)

    @staticmethod
    def resolve_me(root, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

    @staticmethod
    def resolve_is_username_available(root, info, username):
        return not get_user_model().objects.filter(username=username).exists()
