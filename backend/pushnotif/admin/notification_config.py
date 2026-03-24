from django.contrib import admin
from pushnotif.models.notification_config import NotificationConfig


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'delivery_method_template', 'is_enabled')
    search_fields = ('profile__user__username', 'delivery_method_template__notification_template__name')
