from rest_framework import serializers

from forms.models import FormDefinition, FormSubmission


class FormDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormDefinition
        fields = (
            'name', 'slug', 'description', 'form_type', 'status',
            'schema', 'field_config', 'logic_rules', 'scoring', 'prefill',
            'version',
        )
        read_only_fields = ('version', 'status')


class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSubmission
        fields = ('form', 'payload', 'status', 'submitted_by', 'organization')
        read_only_fields = ('submitted_by', 'organization')
