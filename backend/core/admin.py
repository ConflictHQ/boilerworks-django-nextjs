import logging
from email.headerregistry import Address as EmailAddress
from html import escape
from pathlib import Path
from uuid import uuid4

import requests
from core.models import (
    Address,
    ApprovalPropertyWhitelist,
    EmailTemplate,
    GlobalIDLink,
    Interval,
    Link,
    MetabaseChart,
    Notification,
    PinTransaction,
    Profile,
    ResourceFile,
    SharedDirectory,
    SignRequest,
    TemplateModel,
    Upload,
    UserSwitchGroup,
)
from core.models.authorization.principal import (
    PermissionSharedResourcePolicy,
    SharedResourceName,
    SharedResourcePolicy,
    SourceSharedResourcePolicy,
    TargetSharedResourcePolicy,
)
from core.models.internationalization import SiteLabel
from core.models.library.directory import SharedFile
from core.models.process import DataProcess, DataProcessEntity, ProcessStatus
from core.systems import AdminProcessSystem, BaseEmail, EmailRequest
from core.utils.admin import AdminGrapheneUtils, BaseCoreAdmin, obj_to_link, objs_to_links
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.widgets import ForeignKeyRawIdWidget, ManyToManyRawIdWidget
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.models import Session
from django.db import transaction
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from organization.models import Organization

logger = logging.getLogger(__name__)


class VerboseForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    """Shows customisable str representation of the linked object next to the
       raw id field for a ForeignKey or OneToOneField in a django admin change
       form. To customise pass get_str as a keyword argument when initialising
       the widget.
    """

    def __init__(self, *args, **kwargs):
        self.get_str = kwargs.pop('get_str', str)
        super(VerboseForeignKeyRawIdWidget, self).__init__(*args, **kwargs)

    def label_and_url_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(
                self.db).get(**{key: value})
        except (ValueError, self.rel.to.DoesNotExist):
            return '???'

        change_url = reverse(
            "admin:%s_%s_change" % (obj._meta.app_label,
                                    obj._meta.object_name.lower()),
            args=(obj.pk,)
        )
        return '&nbsp;<strong><a href="%s">%s</a></strong>' % (
            change_url, escape(self.get_str(obj)))


class VerboseManyToManyRawIdWidget(ManyToManyRawIdWidget):
    """
    A Widget for displaying ManyToMany ids in the "raw_id" interface rather
    than in a <select multiple> box. Display user-friendly value like the ForeignKeyRawId widget
    """
    template_name = "many_to_many_raw_id_with_references.html"

    def __init__(self, remote_field, attrs=None, *args, **kwargs):
        super().__init__(remote_field, attrs, *args, **kwargs)

    def get_context(self, name, value, attrs):
        context = {
            'widget': {
                'name': name,
                'is_hidden': self.is_hidden,
                'required': self.is_required,
                'value': ','.join(str(key) for key in value),
                'attrs': self.build_attrs(self.attrs, attrs),
                'template_name': self.template_name,
            },
            'references': self.label_and_url_for_value(value)
        }
        if self.admin_site.is_registered(self.rel.model):
            # The related object is registered with the same AdminSite
            context['widget']['attrs']['class'] = "vManyToManyRawIdAdminField"
        return context

    def label_and_url_for_value(self, value):
        values = value
        str_values = []
        labels = []
        field = self.rel.get_related_field()
        key = field.name
        fk_model = self.rel.model
        app_label = fk_model._meta.app_label
        class_name = fk_model._meta.object_name.lower()
        for the_value in values:
            try:
                obj = fk_model._default_manager.using(self.db).get(**{key: the_value})
                url = reverse('admin:{0}_{1}_change'.format(app_label, class_name), args=[obj.id])
                label = escape(smart_str(obj))
                labels.append(label)
                elt = '<a href="{0}" {1}>{2}</a>'.format(
                    url,
                    'onclick="return showAddAnotherPopup(this);" target="_blank"',
                    label
                )
                str_values += [elt]
            except fk_model.DoesNotExist:
                str_values += [u'???']
        return str_values


class ImprovedRawIdFieldsAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = VerboseManyToManyRawIdWidget(db_field.remote_field, self.admin_site)
        else:
            return super().formfield_for_dbfield(db_field, **kwargs)
        kwargs.pop('request')
        return db_field.formfield(**kwargs)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = "user"
    raw_id_fields = 'avatar', 'signature', 'address', 'deleted_by', 'updated_by', 'created_by'


class UserCreationFormCustom(UserCreationForm):

    def __required_quantityinit__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = False


class UserChangeFormCustom(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = False


admin.site.unregister(get_user_model())
admin.site.unregister(Group)


@admin.register(Group)
class PermissionGroupAdmin(GroupAdmin):
    actions = ['clone_selected', 'export_all_groups', 'export_all_groups_permissions']

    def clone_selected(self, request, queryset):
        for group_name in queryset:
            logger.info(f'Creating copy of group {group_name}')
            try:
                with transaction.atomic():
                    group: Group = Group.objects.filter(name=group_name).first()

                    clone: Group = Group.objects.create(name=f'{group_name} (copy)')
                    clone.organizations.set(group.organizations.all())
                    clone.permissions.set(group.permissions.all())
                    clone.save()
                    logger.info(f'Finished creating copy of group {group_name}')
                    messages.info(request, f'Created new group {group_name} (copy)')
            except Exception as e:
                logger.error(e)
                messages.error(request, f'Failed creating copy of group {group_name}')

    @admin.action(description='Export all groups to CSV')
    def export_all_groups(self, request, queryset=None):
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        filename = f"groups_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Group'])
        for organization in Organization.objects.all():
            for group in organization.groups.all().values_list('name', flat=True):
                writer.writerow([
                    f'{organization.slug}|{group}',
                ])

        return response

    @admin.action(description='Export all groups with permissions to CSV')
    def export_all_groups_permissions(self, request, queryset=None):
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        filename = f"groups_permissions_relationships_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        headers = ['Global Identifier', 'Module | Permission']
        group_index_map = {}
        perm_group_index_map = {}
        for org in Organization.objects.all():
            for group_name, perm_id in org.groups.all().values_list('name', 'permissions'):
                column_header = f'{org.slug}|{group_name}'
                if perm_id not in perm_group_index_map:
                    perm_group_index_map[perm_id] = set()
                if column_header not in headers:
                    headers.append(column_header)
                    group_index_map[column_header] = len(headers) - 1
                if perm_id is not None:
                    perm_group_index_map[perm_id].add(group_index_map[column_header])

        writer = csv.writer(response)
        writer.writerow(headers)
        for permission in Permission.objects.all():
            row = [
                      f'{permission.content_type.model}.{permission.content_type.app_label}.{permission.codename}',
                      f'{permission.content_type.app_labeled_name}:{permission.name}'
                  ] + ['False'] * len(group_index_map)

            if permission.id in perm_group_index_map:
                for group_index in perm_group_index_map[permission.id]:
                    row[group_index] = 'True'

            writer.writerow(row)

        return response


class LocationListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Location"
    # Parameter for the filter that will be used in the URL query.
    parameter_name = "location"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            (a.value, a.name) for a in Upload.Location
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        location = request.GET.get('location', None)
        if location:
            return queryset.filter(
                location__exact=location
            )
        return queryset


class UploadDeletedFilter(admin.SimpleListFilter):
    title = 'Is soft deleted'
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'deleted_at'

    def lookups(self, request, model_admin):
        return (
            ('True', 'has been deleted'),
            ('False', 'Still in use'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'False':
            return queryset.filter(deleted_at__isnull=True)
        if self.value() == 'True':
            return queryset.filter(deleted_at__isnull=False)


class UploadForm(forms.ModelForm):
    file = forms.FileField()

    class Meta:
        model = Upload
        fields = '__all__'

    def save(self, commit=True):
        from organization.models import Organization
        organization: Organization = self.cleaned_data['organization'] or self.current_user.profile.organization()
        if not self.instance or not self.instance.public_url:
            upload_location: Upload.Location = Upload.Location[self.cleaned_data['location']]
            uuid = self.cleaned_data.get('uuid', None) or uuid4()
            path = Upload.generate_path(
                upload_location,
                organization=organization,
                target_global_id=self.cleaned_data['target_global_id'],
                uuid=uuid,
                mimetype=self.cleaned_data['content_type'],
            )
            public_url = Upload.generate_pre_signed_url_for_get(
                path,
                content_type=self.cleaned_data['content_type'],
                expire=60
            )
            if upload_location == Upload.Location.PUBLIC:
                public_url = public_url.split('?')[0]
            pre_signed_url = Upload.generate_pre_signed_url_for_put(
                path,
                content_type=self.cleaned_data['content_type'],
                expire=60
            )
            instance = super(UploadForm, self).save(commit=False)
            instance.id = uuid
            instance.pre_signed_url = pre_signed_url
            instance.public_url = public_url
            instance.pre_signed_url = pre_signed_url
            instance.created_by = self.current_user
            instance.location = upload_location.value
            instance.path = path
            if self.files.get('file', None):
                http_response = requests.put(
                    pre_signed_url,
                    data=self.files['file'].read(),
                    headers={'Content-Type': self.cleaned_data['content_type']}
                )
                if http_response.status_code != 200:
                    raise forms.ValidationError('File failed to upload, contact BE engineers if the issue persists.')
            return instance

        return super(UploadForm, self).save(commit=commit)


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin, AdminGrapheneUtils):
    list_display = (
        'id',
        '_public_url',
        '_file_name',
        '_location',
        '_owner_entity',
        'created_at',
        'global_id',
        '_created_by_username',
        '_updated_by_username',
    )
    search_fields = 'id', 'target_global_id', 'created_by__username'
    list_filter = [LocationListFilter, UploadDeletedFilter]
    ordering = '-created_at',
    actions = 'create_file_upload',
    form = UploadForm

    @staticmethod
    def _file_name(obj: Upload):
        return obj.name or (obj.metadata or {}).get('file_name', None) or ''

    @staticmethod
    def _owner_entity(obj: Upload):
        from graphql_relay import from_global_id
        if obj.target_global_id:
            obj_type, obj_id = from_global_id(obj.target_global_id)
            return f'{obj_type} ({obj.target_global_id})'
        return 'General Purpose File'

    @staticmethod
    def _location(obj: Upload):
        return obj.location

    def _public_url(self, obj: Upload):
        return mark_safe(f'<a href="{obj.public_url}" target="_blank">Public URL</a>') if obj.public_url else None

    def _created_by_username(self, obj: Upload):
        if obj.created_by is None:
            return '-'
        return obj.created_by.username

    def _updated_by_username(self, obj: Upload):
        if obj.updated_by is None:
            return '-'
        return obj.updated_by.username

    def get_form(self, request, obj=None, **kwargs):
        fields = [
            'name',
            'content_type',
            'description',
            'metadata',
            'target_global_id',
            'location',
            'deleted_at',
            'updated_by',
            'created_by',
        ]
        if not obj:
            fields.extend([
                'organization',
                'file'
            ])
        kwargs.update({
            'fields': fields
        })
        form = super(UploadAdmin, self).get_form(request, obj, **kwargs)
        if obj:
            disabled_fields = set()  # type: set[str]
            disabled_fields |= {
                'target_global_id',
                'location',
                'content_type'
            }
            for f in disabled_fields:
                if f in form.base_fields:
                    form.base_fields[f].disabled = True
            form.base_fields.pop('file', None)
            form.base_fields.pop('location', None)
        form.current_user = request.user
        return form


class UserAdmin(BaseUserAdmin):
    inlines = ProfileInline,
    form = UserChangeFormCustom
    add_form = UserCreationFormCustom


@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    actions = (
        'add_to_platform_user_group',
        'show_users_permissions',
        'compare_user_permissions',
        'register_in_auth0',
        'reset_password',
        'switch_current_user',
        'anonymize',
        'reset_cache_permissions'
    )
    search_fields = 'username', 'email', 'profile__display_name',

    @admin.action(description='Anonymize user (Note: This action is irreversible)')
    def anonymize(self, request, queryset):
        for user in queryset:
            try:
                Profile.anonymize_user(user)
                messages.info(request, mark_safe(f'Anonymized {obj_to_link(user)}'))
            except Exception as e:
                logger.exception(f'Failed to anonymize {user.username}: {e}')
                messages.error(request, mark_safe(f'Failed to anonymize {obj_to_link(user)}: {e}'))

    def reset_cache_permissions(self, request, queryset):
        from core.systems.permissions import AllPermissions
        AllPermissions.reset()
        messages.info(request, 'Permissions cache reset')

    def show_users_permissions(self, request, queryset):
        user_ids = set()
        for user in queryset:
            user_ids.add(user.pk)

        reversed_url = '/app/core/core/user-permissions-tree-view/'
        query_string = '&'.join([f'ids={user_id}' for user_id in user_ids])
        url = f'{reversed_url}?{query_string}'
        return HttpResponseRedirect(url)

    @admin.action(description='Compare user group permissions')
    def compare_user_permissions(self, request, queryset):
        """
        Admin action to compare group permissions between selected users.
        Redirects to a dedicated comparison page where users can select a base user.
        """
        user_ids = list(queryset.values_list('pk', flat=True))

        if len(user_ids) < 2:
            messages.warning(request, 'Please select at least 2 users to compare permissions.')
            return

        query_string = '&'.join([f'ids={user_id}' for user_id in user_ids])
        url = f'/app/core/core/compare-user-permissions/?{query_string}'
        return HttpResponseRedirect(url)

    def switch_current_user(self, request, queryset):
        if not request.user.is_superuser:
            messages.error(request, 'Only superuser can switch user')
            return

        from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
        try:
            from django.contrib.auth import HASH_SESSION_KEY as AUTH_HASH_SESSION_KEY
        except ImportError:
            AUTH_HASH_SESSION_KEY = '_auth_user_hash'

        other_user = queryset.first()
        if request.session.get(settings.SWITCHED_FROM_USER):
            if other_user.pk == request.session[settings.SWITCHED_FROM_USER]:
                request.session[settings.SWITCHED_FROM_USER] = None
        else:
            request.session[settings.SWITCHED_FROM_USER] = request.user.pk

        request.user = other_user
        request.session[AUTH_SESSION_KEY] = other_user.pk
        request.session[AUTH_HASH_SESSION_KEY] = other_user.get_session_auth_hash()
        request.session.save()
        messages.info(request, f'Current user switched to {other_user.username}')

    def add_to_platform_user_group(self, request, queryset):
        group = Group.objects.filter(name='Platform Users').first()
        for user in queryset:
            user.groups.add(group)

    def register_in_auth0(self,  request, queryset):
        for user in queryset:
            try:
                user.profile.register_in_auth0()
                messages.info(request, f'Registered {user.email} in Auth0')
            except Exception as e:
                logger.exception(f'Failed to register {user.email} in Auth0: {e}')
                messages.error(request, f'Failed to register {user.email} in Auth0: {e}')

    def reset_password(self, request, queryset):
        for user in queryset:
            try:
                user.profile.request_reset_password()
                messages.info(request, f'Reset password for {user.email}')
            except Exception as e:
                logger.exception(f'Failed to reset password for {user.email}: {e}')
                messages.error(request, f'Failed to reset password for {user.email}: {e}')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin, AdminGrapheneUtils):
    list_display = '__str__',


class GlobalIDLinkInline(admin.StackedInline):
    model = Notification.related_gids.through
    show_change_link = True
    extra = 1
    raw_id_fields = 'globalidlink',


@admin.register(GlobalIDLink)
class GlobalIDLinkAdmin(BaseCoreAdmin):
    list_display = 'gid', 'name',
    search_fields = 'gid', 'name',
    readonly_fields = '_object',

    def _object(self, obj: GlobalIDLink):
        return obj_to_link(obj.get_instance())


@admin.register(Link)
class LinkAdmin(BaseCoreAdmin):
    list_display = 'url', 'title',
    search_fields = 'url', 'title',


@admin.register(Notification)
class NotificationAdmin(BaseCoreAdmin):
    list_display = 'created_by', 'user', 'subject', 'status', 'global_id'
    search_fields = 'user__username', 'subject', 'message', 'created_by__username',
    filter_horizontal = 'related_gids',
    ordering = '-created_at',
    list_filter = 'status',
    readonly_fields = '_related_gids',
    raw_id_fields = 'related_gids',

    def _related_gids(self, obj: Notification):
        return objs_to_links(obj.related_gids.all())


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin, AdminGrapheneUtils):
    search_fields = 'user__username', 'display_name', 'user__email'
    list_display = '_profile', '_username', '_user_gid', '_has_pin', 'pk',
    readonly_fields = '_has_pin',

    def _profile(self, obj: Profile):
        return obj

    def _user_gid(self, obj: Profile):
        return self.global_id(obj.user) if obj.user else None

    def _username(self, obj: Profile):
        return obj.user.username if obj.user else None

    def _has_pin(self, obj: Profile):
        return obj.has_pin()


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin, AdminGrapheneUtils):
    list_display = 'name', 'content_type', 'codename', 'global_id',
    list_filter = ('content_type',)
    search_fields = 'name', 'codename',
    actions = ['export_all_permissions']

    @admin.action(description='Export all permissions to CSV')
    def export_all_permissions(self, request, queryset=None):
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        filename = f"permissions_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Name', 'Module | Permission', 'Label', 'Global Identifier'])

        for permission in Permission.objects.all().order_by('id'):
            writer.writerow([
                permission.name,
                permission.content_type.app_labeled_name,
                permission.codename,
                f'{permission.content_type.model}.{permission.content_type.app_label}.{permission.codename}',
            ])

        return response


class ProcessDataModelForm(ModelForm):
    data_file = forms.FileField(required=False)
    language_code = forms.ChoiceField(choices=settings.LANGUAGES,
                                      required=False,
                                      help_text="Use only for importing Site Labels, ignore otherwise")

    class Meta:
        readonly_fields = ('file_type')
        exclude = ('uploaded_file',)


@admin.register(DataProcess)
class DataProcessAdmin(BaseCoreAdmin):
    list_display = 'batch', 'status', 'created_at'
    list_filter = ['entity_type', 'status']
    form = ProcessDataModelForm
    search_fields = ['batch']
    actions = ('process_upsert', 'process_overwrite', 'make_pending')
    ordering = '-created_at',

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['status_date', 'status_description', 'file_type', 'entity_type']
        return ['status_date', 'status_description']

    def save_model(self, request, obj, form, change):
        file = request.FILES.get('data_file', None)

        if obj.file_name is None and file is not None:
            obj.file_name = request.FILES['data_file'].name

        if file:
            print(file.size, Path(__file__).absolute())
        return AdminProcessSystem.load_data(request, entity_type=obj.entity_type,)

    @admin.action(description='Process Data Upsert')
    def process_upsert(self, request, queryset):
        for record in queryset:
            AdminProcessSystem.process(record, request.user, False)

    @admin.action(description='Change Status to Pending')
    def make_pending(self, request, queryset):
        AdminProcessSystem.change_status(queryset, status=ProcessStatus.PENDING)


@admin.register(DataProcessEntity)
class DataProcessEntityAdmin(BaseCoreAdmin):
    list_display = 'process', 'status', 'status_date'
    readonly_fields = ('created_by', 'created_at', 'line_number', 'process', 'status_date', 'updated_by', 'version')
    search_fields = ['process__batch']
    list_filter = ['process__entity_type', 'status']


@admin.register(SiteLabel)
class SiteLabelAdmin(BaseCoreAdmin, AdminGrapheneUtils):
    search_fields = ['key']
    list_display = 'key', 'locale'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    actions = ['flush_cache', 'check_opensearch_connection', 'create_opensearch_index', 'delete_opensearch_index']
    list_display = ('session_key', 'username', 'expire_date')
    search_fields = ['session_key']
    list_filter = ['expire_date']
    readonly_fields = ('decoded',)

    def decoded(self, obj):
        return obj.get_decoded()

    def username(self, obj):
        from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
        auth_user_id = obj.get_decoded().get(AUTH_SESSION_KEY)
        if not auth_user_id:
            return None
        user = get_user_model().objects.filter(pk=auth_user_id).first()
        return user.username if user else None

    @admin.action(description='Flush redis cache')
    def flush_cache(self, request, queryset):
        from django.core.cache import cache
        cache.clear()

    @admin.action(description='Run search index session')
    def create_opensearch_index(self, request, queryset):
        from django.core.management import call_command
        from opensearchpy.exceptions import ConflictError
        try:
            # Create OpenSearch indices
            logger.info("Create OpenSearch indices")
            call_command('opensearch', 'index', 'create', '--force')
            logger.info("Successfully created OpenSearch indices")

            # Index documents
            logger.info("Create OpenSearch docs")
            call_command('opensearch', 'document', 'index', '--force')
            logger.info("Successfully indexed documents to OpenSearch")

            messages.success(request, 'Successfully created and indexed OpenSearch indices')
        except (SystemExit, ConflictError) as e:
            # Index doesn't exist - this is not an error, just log it
            logger.info(f"OpenSearch index already exists {e}")
            messages.warning(request, 'OpenSearch index already exists')
        except Exception as e:
            logger.exception(f'Failed to run search index session: {e}. Please try to delete any previous indices')
            messages.error(request, f'Failed to run search index session: {str(e)}')

    @admin.action(description='Delete search index session')
    def delete_opensearch_index(self, request, queryset):
        from django.core.management import call_command
        from opensearchpy.exceptions import NotFoundError
        try:
            # Delete any previous indexes if any
            logger.info("Deleting previous OpenSearch indices")
            call_command('opensearch', 'index', 'delete', '--force')
            logger.info("Successfully deleted previous OpenSearch indices")
            messages.success(request, 'Successfully deleted OpenSearch indices')
        except (SystemExit, NotFoundError) as e:
            # Index doesn't exist - this is not an error, just log it
            logger.info(f"OpenSearch index doesn't exist or was already deleted {e}")
            messages.warning(request, 'OpenSearch index does not exist or was already deleted')
        except Exception as e:
            logger.exception(f'Failed to delete search index: {e}')
            messages.error(request, f'Failed to delete search index: {str(e)}')

    @admin.action(description='Check opensearch connection')
    def check_opensearch_connection(self, request, queryset):
        from opensearchpy import connections

        try:
            client = connections.get_connection()
            client.info()
            logger.info(f"Successfully connected to OpenSearch {client.info()}.")
        except Exception as e:
            logger.info(f"Failed to connect to OpenSearch: {e}")


@admin.register(TemplateModel)
class TemplateModelAdmin(admin.ModelAdmin):
    pass


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = 'id', 'app_label', 'header_template', 'body_template'
    change_list_template = 'core/emails/change_list.html'
    actions = "send_email",
    readonly_fields = 'id', 'app_label', 'classname', 'member', 'parameters', 'header_template', 'body_template'

    @staticmethod
    def _to_email_address_list(value) -> list[EmailAddress]:
        """
        Converts the given string in a list of email addresses.
        """
        return [EmailAddress(addr_spec=address) for address in value.split(',') if address]

    @admin.action(description="Send Test Email")
    def send_email(self, request, queryset):
        """
        Action to send a sample email to the provided addresses.
        """
        recipients = self._to_email_address_list(request.POST['to-email'])
        carbon_copy = self._to_email_address_list(request.POST['cc-email'])
        blind_carbon_copy = self._to_email_address_list(request.POST['bcc-email'])
        for record in queryset:
            email_template: BaseEmail = BaseEmail.get_email_by_identifier(record.id)
            parameters = email_template.parameters_sample()
            email_template.send(
                request=EmailRequest(
                    subject=f'[{email_template}] Test',
                    recipients=recipients,
                    carbon_copy=carbon_copy,
                    blind_carbon_copy=blind_carbon_copy
                ),
                parameters=parameters,
            )


@admin.register(PinTransaction)
class PinTransactionAdmin(admin.ModelAdmin):
    list_display = 'user', 'proxy_user', 'kind', 'created_at',
    list_filter = 'kind',
    ordering = '-created_at',

    readonly_fields = 'transaction', 'kind', 'user', 'proxy_user', 'data', 'sealed', \
        'data', 'created_at', 'updated_at'


@admin.register(SignRequest)
class SignRequestAdmin(BaseCoreAdmin):
    list_display = 'user', 'status', 'linked', 'created_at', 'global_id'
    list_filter = 'status',
    ordering = '-created_at',
    raw_id_fields = ('user', 'sign_requested', 'signed_by', 'deleted_by', 'cancel_by',
                     'updated_by', 'created_by', 'global_id_link')
    readonly_fields = 'cancel_by', 'linked',
    search_fields = 'user__username', 'sign_requested__username', 'status',

    def linked(self, obj):
        if obj.global_id_link:
            return obj_to_link(obj.global_id_link.get_instance())


admin.site.register(ResourceFile)
admin.site.register(UserSwitchGroup)


@admin.register(Interval)
class IntervalAdmin(admin.ModelAdmin):
    pass


# @admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("__str__", "interval", "lower_bound", "upper_bound")
    list_filter = ('interval',)


class SourceSharedResourcePolicyInline(admin.TabularInline):
    model = SourceSharedResourcePolicy
    fields = "policy", "resource"
    show_change_link = True
    extra = 0


class TargetSharedResourcePolicyInline(admin.TabularInline):
    model = TargetSharedResourcePolicy
    fields = "policy", "resource"
    show_change_link = True
    extra = 0


class SharedFileInline(admin.TabularInline):
    model = SharedFile
    fields = "file", "path"
    show_change_link = True
    extra = 0
    raw_id_fields = "file",


class SharedDirectoryInline(admin.TabularInline):
    model = SharedDirectory
    fields = "display_name", "name", "path"
    show_change_link = True
    extra = 0


class PermissionSharedResourcePolicyInline(admin.TabularInline):
    model = PermissionSharedResourcePolicy
    fields = "permission",
    show_change_link = True
    extra = 0


@admin.register(SharedResourceName)
class SharedResourceNameAdmin(admin.ModelAdmin):
    list_display = "name", "global_id", "content_type", "content_object", "object_id"
    list_filter = "content_type",
    readonly_fields = list_display
    inlines = [
        SourceSharedResourcePolicyInline,
        TargetSharedResourcePolicyInline
    ]


@admin.register(SharedResourcePolicy)
class SharedResourcePolicyAdmin(admin.ModelAdmin):
    list_display = "name", "_source_resources", "_target_resources", "_permissions"
    inlines = [
        SourceSharedResourcePolicyInline,
        TargetSharedResourcePolicyInline,
        PermissionSharedResourcePolicyInline
    ]

    def _source_resources(self, obj: SharedResourcePolicy):
        return objs_to_links(obj.source_resources.all())

    def _target_resources(self, obj: SharedResourcePolicy):
        return objs_to_links(obj.target_resources.all())

    def _permissions(self, obj: SharedResourcePolicy):
        return objs_to_links(obj.permissions.all())


@admin.register(SharedDirectory)
class SharedDirectoryAdmin(BaseCoreAdmin, AdminGrapheneUtils):
    list_display = "display_name", "name", "path", "_shared_resource_name", "global_id"
    inlines = [
        SharedDirectoryInline,
        SharedFileInline,
    ]
    raw_id_fields = "owners", "icon", "parent",
    search_fields = "display_name", "name", "path"

    def _shared_resource_name(self, obj: SharedDirectory):
        return obj_to_link(obj.shared_resource_name)


@admin.register(SharedFile)
class SharedFileAdmin(BaseCoreAdmin, AdminGrapheneUtils):
    list_display = "parent", "file", "global_id"
    raw_id_fields = "file", "parent",
    search_fields = "file__name", "parent__name"


@admin.register(ApprovalPropertyWhitelist)
class ApprovalPropertyWhitelistAdmin(admin.ModelAdmin):

    list_display = 'app_label', 'model_name', 'attribute', 'enabled'
    search_fields = 'content_type__model', 'attribute'

    @staticmethod
    def app_label(obj):
        return obj.content_type.app_label

    @staticmethod
    def model_name(obj):
        return obj.content_type.model

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'content_type':
            from django.contrib.contenttypes.models import ContentType
            kwargs["queryset"] = ContentType.objects.filter(app_label__in=['core'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(MetabaseChart)
class MetabaseChartAdmin(admin.ModelAdmin):
    list_display = 'id', 'type', 'metabase_chart_id', 'title', 'created_at'
    search_fields = 'id', 'type', 'created_by__username'
    ordering = '-created_at',
