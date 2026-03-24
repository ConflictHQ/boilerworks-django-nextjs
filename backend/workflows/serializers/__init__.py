from rest_framework import serializers

from workflows.models import WorkflowDefinition


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = ('name', 'slug', 'description', 'model_label', 'states', 'transitions', 'is_enabled')
