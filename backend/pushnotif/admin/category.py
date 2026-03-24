from django.contrib import admin

from ..models import DeliveryMethod, NotificationCategory


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = 'name', 'display_name'


@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    pass


__all__ = ['DeliveryMethod', 'NotificationCategory']
