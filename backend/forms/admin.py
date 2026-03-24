from core.utils.admin import BaseCoreAdmin
from django.contrib import admin

from .models import FormDefinition, FormSubmission


@admin.register(FormDefinition)
class FormDefinitionAdmin(BaseCoreAdmin):
    list_display = ('name', 'slug', 'version', 'status', 'form_type', 'published_at', 'created_at')
    list_filter = ('status', 'form_type')
    search_fields = ('name', 'slug')
    readonly_fields = ('version', 'published_at', 'published_by', 'created_at', 'created_by', 'updated_at', 'updated_by')


@admin.register(FormSubmission)
class FormSubmissionAdmin(BaseCoreAdmin):
    list_display = ('pk', 'form', 'status', 'submitted_by', 'submitted_at')
    list_filter = ('status', 'form__slug')
    search_fields = ('form__name', 'form__slug')
    readonly_fields = ('form', 'payload', 'submitted_by', 'submitted_at')
