from core.utils.admin import BaseCoreAdmin
from core.widgets import JSONEditorWidget
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from .models import FormDefinition, FormStatus, FormSubmission


class FormSubmissionInline(admin.TabularInline):
    model = FormSubmission
    extra = 0
    fields = ('pk', 'status', 'submitted_by', 'submitted_at')
    readonly_fields = ('pk', 'status', 'submitted_by', 'submitted_at')
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FormDefinition)
class FormDefinitionAdmin(BaseCoreAdmin):
    list_display = ('name', 'slug', 'version', 'status_badge', 'form_type', 'is_public', 'submission_count', 'published_at', 'created_at')
    list_filter = ('status', 'form_type', 'is_public')
    search_fields = ('name', 'slug')
    formfield_overrides = {models.JSONField: {'widget': JSONEditorWidget}}
    readonly_fields = ('version', 'published_at', 'published_by', 'created_at', 'created_by', 'updated_at', 'updated_by')
    inlines = [FormSubmissionInline]
    actions = ['publish_forms', 'archive_forms', 'clone_forms']

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'form_type', 'is_public')}),
        ('Schema', {'fields': ('schema', 'field_config', 'logic_rules', 'scoring', 'prefill'), 'classes': ('collapse',)}),
        ('Notifications', {'fields': ('notification_config',), 'classes': ('collapse',)}),
        ('Versioning', {'fields': ('version', 'status', 'published_at', 'published_by')}),
        ('Tracking', {'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'), 'classes': ('collapse',)}),
    )

    def status_badge(self, obj):
        colors = {
            FormStatus.DRAFT: '#6b7280',
            FormStatus.PUBLISHED: '#22c55e',
            FormStatus.ARCHIVED: '#f59e0b',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj) or ())
        if obj and obj.status != FormStatus.DRAFT:
            # Published/archived forms are read-only except status
            readonly.extend(['name', 'slug', 'description', 'form_type', 'schema', 'field_config', 'logic_rules', 'scoring', 'prefill'])
        return tuple(readonly)

    @admin.action(description='Publish selected draft forms')
    def publish_forms(self, request, queryset):
        published = 0
        for form in queryset.filter(status=FormStatus.DRAFT):
            form.publish(request.user)
            published += 1
        self.message_user(request, f'{published} form(s) published.')

    @admin.action(description='Archive selected published forms')
    def archive_forms(self, request, queryset):
        archived = 0
        for form in queryset.filter(status=FormStatus.PUBLISHED):
            form.archive()
            archived += 1
        self.message_user(request, f'{archived} form(s) archived.')

    @admin.action(description='Clone selected forms as new draft')
    def clone_forms(self, request, queryset):
        cloned = 0
        for form in queryset:
            form.new_draft(request.user)
            cloned += 1
        self.message_user(request, f'{cloned} form(s) cloned as new draft.')


@admin.register(FormSubmission)
class FormSubmissionAdmin(BaseCoreAdmin):
    list_display = ('pk', 'form', 'status', 'submitted_by', 'submitted_at', 'has_attachments')
    list_filter = ('status', 'form__slug')
    search_fields = ('form__name', 'form__slug')
    readonly_fields = ('form', 'payload', 'submitted_by', 'submitted_at', 'secure_payload', 'attachments')

    def has_attachments(self, obj):
        return obj.attachments.exists()
    has_attachments.boolean = True
    has_attachments.short_description = 'Files'
