"""
Auth1 Models
"""

from django.conf import settings
from django.db import models


class UserInfo(models.Model):
    """
    User Info Model.

    This data is provided by Auth0 API on the callback.

    We store this information in a table in the database, and eventually we
    join our user into the given record.
    """

    internal_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='remote_users')

    given_name = models.CharField(max_length=1024)
    family_name = models.CharField(max_length=1024)
    nickname = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024)
    picture = models.CharField(max_length=1024)
    locale = models.CharField(max_length=1024)
    updated_at = models.DateTimeField()
    email = models.EmailField(db_index=True)
    email_verified = models.BooleanField()
    iss = models.URLField()
    aud = models.CharField(max_length=128)
    iat = models.IntegerField()
    exp = models.IntegerField()
    sub = models.CharField(max_length=128, primary_key=True)
    sid = models.CharField(max_length=128)
    nonce = models.CharField(max_length=128)


class Authentication(models.Model):
    """
    Authentication Model, which stores the token provided by Auth0

    At this moment we do not store this information in the database.

    We eventually can store this information in a Cache.
    """

    access_token = models.CharField(max_length=8 * 1024)
    id_token = models.CharField(max_length=8 * 1024, primary_key=True)
    scope = models.CharField(max_length=8 * 1024, null=True)
    iat = models.IntegerField(null=True)
    token_type = models.CharField(max_length=32, null=True)
    expires_at = models.IntegerField(null=True)
    expires_in = models.IntegerField(default=0, null=True)

    userinfo = models.ForeignKey(
        UserInfo,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='userinfos'
    )
