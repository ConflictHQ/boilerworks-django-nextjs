from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False, help_text="Id of the user to be modified.")
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = ['email', 'id', 'first_name', 'last_name', 'username', 'is_active']
