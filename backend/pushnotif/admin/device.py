from django.contrib import admin

from ..models import DeviceToken


@admin.register(DeviceToken)
class DeviceAdmin(admin.ModelAdmin):
    list_display = 'name', 'recipient', 'device_token', 'created_at',
    search_fields = ('name', 'recipient__username')
