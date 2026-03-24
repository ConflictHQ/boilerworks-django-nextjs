"""
Auth1 Admin Model.
"""
from auth1.models import Authentication, UserInfo
from django.contrib import admin


class AuthenticationInline(admin.TabularInline):
    """
    Authentication Inline
    """
    model = Authentication


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    """
    User Info Model Admin
    """
    readonly_fields = (
        'given_name',
        'family_name',
        'nickname',
        'name',
        'email',
        'email_verified',
        'locale',
        'updated_at',
        'nonce',
        'sid',
        'sub',
        'exp',
        'iat',
        'aud',
        'iss',
        'picture',
    )
    list_display = (
        'pk',
        'given_name',
        'family_name',
        'nickname',
        'email',
        'email_verified',
        'locale',
        'updated_at',
        'internal_user',
    )
    search_fields = (
        'given_name',
        'family_name',
        'nickname',
        'email',
        'internal_user__username',
        'internal_user__first_name',
        'internal_user__last_name',
    )
    list_filter = 'email_verified',
    inlines = [AuthenticationInline]
