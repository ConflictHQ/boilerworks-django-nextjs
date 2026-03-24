from core.models import MetabaseChart
from core.serializers.restricted_model_serializer import FieldRestrictedSerializer
from rest_framework import serializers


class MetabaseChartSerializer(FieldRestrictedSerializer):
    id = serializers.CharField(required=False, allow_null=False,
                               help_text="The internal id of the MetabaseChart.")
    type = serializers.CharField(required=True, allow_null=False,
                                 help_text="The type of the chart in Metabase.")
    metabase_chart_id = serializers.IntegerField(required=True, allow_null=False,
                                                 help_text="The chart id in Metabase.")
    title = serializers.CharField(required=True, allow_null=False,
                                  help_text="The title of the chart in Metabase.")
    description = serializers.CharField(required=False, allow_null=False,
                                        help_text="Internal short description of the chart.")

    class Meta(FieldRestrictedSerializer.Meta):
        model = MetabaseChart

    def create(self, validated_data):
        instance = MetabaseChart.objects.create(**validated_data)
        return instance
