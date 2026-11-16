from core.models import SupersetDashboard
from core.serializers.restricted_model_serializer import FieldRestrictedSerializer
from rest_framework import serializers


class SupersetDashboardSerializer(FieldRestrictedSerializer):
    embedded_id = serializers.UUIDField(required=True, allow_null=False,
                                        help_text='Embedded dashboard UUID from Superset ("Embed dashboard").')
    title = serializers.CharField(required=True, allow_null=False, max_length=250,
                                  help_text='Title shown above the embedded dashboard.')
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=250,
                                        help_text='Internal short description of the dashboard.')
    order = serializers.IntegerField(required=False, min_value=0,
                                     help_text='Position in the analytics page (lowest first).')
    rls_clause = serializers.CharField(required=False, allow_blank=True,
                                       help_text='Optional row-level security clause for guest tokens.')

    class Meta(FieldRestrictedSerializer.Meta):
        model = SupersetDashboard

    def create(self, validated_data):
        return SupersetDashboard.objects.create(**validated_data)
