from django.contrib import admin
from django.db.models import QuerySet

from ..models import EmailNotification, NotificationTemplate, PushNotification, SMSNotification
from ..models.notification import DeliveryMethodNotificationTemplate, NotificationEvent, NotificationEventMethod


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = 'id', 'recipient', 'sender', 'status', 'created_at'
    search_fields = ['recipient__username', 'sender__username']
    ordering = ['-created_at']
    actions = ['resend_notifications', 'cleanup_old_notifications']

    @admin.action(description='Resend Notifications')
    def resend_notifications(self, request, queryset: QuerySet[NotificationEvent]):
        for event in queryset:
            event.send()


@admin.register(NotificationEventMethod)
class NotificationEventMethodAdmin(admin.ModelAdmin):
    list_display = 'id', 'notification_event', 'delivery_method', 'status', 'created_at'
    search_fields = ['notification_event__recipient__username', 'notification_event__sender__username']
    ordering = ['-created_at']
    actions = ['resend_notifications', 'cleanup_old_notifications']

    @admin.action(description='Resend Notifications')
    def resend_notifications(self, request, queryset: QuerySet[NotificationEventMethod]):
        for method in queryset:
            method.send()


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = 'id', 'recipient', 'title', 'updated_at', 'sent_at'
    search_fields = ['recipient__username']
    actions = ['resend_notifications']
    ordering = ['-updated_at', '-created_at']

    @admin.action(description='Resend Notifications')
    def resend_notifications(self, request, queryset: QuerySet[SMSNotification]):
        for notification in queryset:
            notification.send()


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = 'id', 'recipient', 'title', 'updated_at', 'sent_at'
    search_fields = ['recipient__username']
    actions = ['resend_notifications']
    ordering = ['-updated_at', '-created_at']


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = 'id', 'recipient', 'title', 'updated_at', 'category', 'state'
    search_fields = ['recipient__username']
    actions = ['resend_notifications']
    ordering = ['-updated_at', '-created_at']

    @admin.action(description='Resend Notifications')
    def resend_notifications(self, request, queryset: QuerySet[PushNotification]):
        for notification in queryset:
            from config.celery import debug_task
            debug_task.delay()
            notification.send()


class DeliveryMethodNotificationTemplateAdmin(admin.StackedInline):
    model = DeliveryMethodNotificationTemplate
    readonly_fields = 'delivery_method', 'header_template', 'body_template'
    fields = readonly_fields + ('never_send_notification', 'always_send_notification',)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    inlines = [DeliveryMethodNotificationTemplateAdmin]
