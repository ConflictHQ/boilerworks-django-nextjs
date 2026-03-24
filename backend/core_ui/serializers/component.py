from core.serializers import FieldRestrictedSerializer
from core_ui.models import Component, ComponentRelationship
from django.contrib.auth.models import Group
from rest_framework import serializers


class ChildComponentReferenceSerializer(serializers.Serializer):
    sort_order = serializers.IntegerField(help_text="The order against other child components")
    child_component = serializers.CharField(help_text="Global Id of children component.")


class ComponentSerializer(FieldRestrictedSerializer):
    children = ChildComponentReferenceSerializer(many=True, required=False, allow_null=True, write_only=True)
    created_by_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    groups = serializers.ListField(
        required=False,
        allow_null=True,
        child=serializers.CharField(),
        help_text='List of permission groups whitelisted to "view" the component.'
    )
    id = serializers.CharField(required=False, allow_null=False, help_text="The id of the component to be use updated.")
    updated_by_id = serializers.CharField(max_length=50, required=False, allow_null=True)

    class Meta:
        model = Component
        exclude = [
            'created_at', 'deleted_at', 'deleted_by', 'permissions', 'updated_at', 'version'
        ]

    def create(self, validated_data):
        children = validated_data.pop('children', [])
        groups = validated_data.pop('groups', [])
        instance = Component.objects.create(**validated_data)
        instance.syn_permissions()
        view_permission = instance.permissions.get(codename=f'view_{instance.slug}')
        for group in groups:
            Group.objects.get(id=group).permissions.add(view_permission)
        child_records = []
        for child in children:
            child_records.append(
                ComponentRelationship(
                    parent_id=instance.id,
                    order=child['sort_order'],
                    child_id=child['child_component']
                )
            )
        ComponentRelationship.objects.bulk_create(child_records)
        return instance

    def update(self, instance: Component, validated_data):
        new_groups = validated_data.pop('groups', None)
        children = validated_data.pop('children', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.syn_permissions()
        if children:
            ComponentRelationship.objects.filter(parent=instance).delete()
            child_records = []
            for child in children:
                child_records.append(
                    ComponentRelationship(
                        parent_id=instance.id,
                        order=child['sort_order'],
                        child_id=child['child_component']
                    )
                )
            ComponentRelationship.objects.bulk_create(child_records)
        if new_groups:
            view_permission = instance.permissions.get(codename=f'view_{instance.slug}')
            former_groups = Group.objects.filter(
                permissions__codename__exact=view_permission.codename).exclude(
                id__in=new_groups
            )
            for former_group in former_groups:
                former_group.permissions.remove(view_permission)
            for group in new_groups:
                Group.objects.get(id=group).permissions.add(view_permission)
        instance.save()
        return instance
