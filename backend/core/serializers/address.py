from core.models import Address
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ['created_at', 'created_by', 'updated_at', 'updated_by', 'version']
