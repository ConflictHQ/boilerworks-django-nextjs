from django.contrib import admin

from ..models import DeepLink, DeepLinkUrlTemplate


class DeepLinkUrlTemplateAdmin(admin.StackedInline):
    model = DeepLinkUrlTemplate
    readonly_fields = 'url_template', 'delivery_method',
    fields = readonly_fields


@admin.register(DeepLink)
class DeepLinkAdmin(admin.ModelAdmin):
    list_display = 'name', 'display_name', 'content_type'
    inlines = [DeepLinkUrlTemplateAdmin]
