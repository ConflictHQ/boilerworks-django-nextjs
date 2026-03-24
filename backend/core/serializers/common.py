import datetime

import core
from core.models import GlobalIDLink, Link
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from rest_framework import serializers


class TimedeltaField(serializers.FloatField):
    """
    Custom field to serialize a timedelta as total seconds.
    """
    def __init__(self, **kwargs):
        kwargs['help_text'] = kwargs.get('help_text', 'Time in seconds')
        kwargs['validators'] = kwargs.get('validators', [MinValueValidator(datetime.timedelta(seconds=0))])
        super().__init__(**kwargs)

    def to_representation(self, value):
        """
        Convert the timedelta to total seconds.
        """
        if not isinstance(value, datetime.timedelta):
            raise TypeError("Expected a timedelta instance, but got {} instead.".format(type(value).__name__))
        return value.total_seconds()

    def to_internal_value(self, data):
        """
        Convert total seconds back to a timedelta.
        """
        try:
            return datetime.timedelta(seconds=float(data))
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError("Invalid value for timedelta: {}".format(e))


class SlugToObjectField(serializers.Field):
    """
    Custom field to convert a slug into a model instance.
    """
    def __init__(self, queryset, slug_field='slug', **kwargs):
        self.queryset = queryset
        self.slug_field = slug_field
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        Convert the input slug into a model instance.
        """
        try:
            # Get the object based on the slug
            obj = self.queryset.get(**{self.slug_field: data})
            return obj
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"Object with {self.slug_field} '{data}' does not exist.")

    def to_representation(self, value):
        """
        Convert the model instance back to its slug representation.
        """
        return getattr(value, self.slug_field)


class GIDToObjectField(serializers.Field):
    """
    Custom field to convert a slug into a model instance.
    """
    class Info:
        def __init__(self, context, return_type):
            self.context = context
            self.return_type = return_type

    def __init__(self, model, **kwargs):
        from graphene_django.registry import get_global_registry
        registry = get_global_registry()
        self.schema_type = registry.get_type_for_model(model)
        self.return_type = self.schema_type
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        Convert the input gid into a model instance.
        """
        info = self.Info(self.context['request'], self.return_type)
        return self.schema_type.get_object(info, data, raise_not_found=True)

    def to_representation(self, value):
        """
        Convert the model instance back to its gid representation.
        """
        return self.schema_type.to_global_id(value)


class GIDToPkField(serializers.Field):
    """
    Custom field to convert a slug into a model instance.
    """
    class Info:
        def __init__(self, context, return_type):
            self.context = context
            self.return_type = return_type

    def __init__(self, model, **kwargs):
        from graphene_django.registry import get_global_registry
        registry = get_global_registry()
        self.schema_type = registry.get_type_for_model(model)
        self.return_type = self.schema_type
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        Convert the input gid into a model instance.
        """
        info = self.Info(self.context['request'], self.return_type)
        return self.schema_type.get_object(info, data, raise_not_found=True).pk

    def to_representation(self, value):
        """
        Convert the model instance back to its gid representation.
        """
        return self.schema_type.to_global_id(value)


class LinkSerializer(serializers.ModelSerializer):
    id = GIDToPkField(model=Link, required=False)

    class Meta:
        model = Link
        fields = ['id', 'title', 'url', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all models.
    """
    id = serializers.CharField(required=False, help_text="Global id of the entity")
    links = LinkSerializer(
        required=False,
        many=True,
        help_text='List of links related to this competency'
    )  # Adding links field

    class Meta:
        model = core.models.BaseCoreModel
        fields = ('name', 'description',)

    def validate(self, data):
        """
        Validate the data.
        """
        if hasattr(self.Meta.model, 'validate_data'):
            return self.Meta.model.validate_data(data)
        return data

    def create(self, validated_data):
        links_data = validated_data.pop('links', [])  # Extract nested links data
        parent = super().create(validated_data)  # Create the parent instance
        self._update_or_create_link(parent, links_data)
        return parent

    def update(self, instance, validated_data):
        links_data = validated_data.pop('links', None)  # Extract nested links data
        parent = super().update(instance, validated_data)  # Update the parent instance
        self._update_or_create_link(parent, links_data)
        return parent

    def _update_or_create_link(self, instance, links):
        """
        Update or create a link for the instance.
        """
        if 'links' not in self.Meta.fields:  # Skip if links field is not in the serializer
            return instance

        if links is not None:
            # Clear existing links
            instance.links.clear()

            # Add new links
            for link_data in links:
                url = link_data.pop('url')
                link, _ = Link.objects.update_or_create(url=url, defaults=link_data)

                instance.links.add(link)


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = GlobalIDLink
        fields = ['app_label', 'gid', 'name', 'description']
