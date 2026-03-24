import logging
from dataclasses import dataclass
from typing import Optional

from django.apps import AppConfig
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError, models
from django.db.models import Model, QuerySet
from django.utils.functional import cached_property

from .delivery_method import DeliveryMethod, DeliveryMethods

logger = logging.getLogger(__name__)


@dataclass
class DeepLinkDefinition:
    model: type
    webapp_format: str
    mobile_format: str

    @cached_property
    def identifier(self) -> str:
        return f'deeplink://{self.content_type.app_label}/{self.content_type.model}'

    @cached_property
    def content_type(self) -> ContentType:
        return ContentType.objects.get_for_model(self.model)

    def register(self, app_config: AppConfig):
        queryset = DeepLink.objects.filter(name=self.identifier)
        if not queryset.exists():
            DeepLink.objects.create(
                name=self.identifier,
                display_name=f'DeepLink for {self.content_type.app_label}/{self.content_type.model}',
                content_type=self.content_type,
            )
        deep_link: DeepLink = queryset.first()
        templates: dict[DeliveryMethods, str] = {
            DeliveryMethods.EMAIL: self.webapp_format,
            DeliveryMethods.SMS: self.webapp_format,
            DeliveryMethods.ANDROID: self.mobile_format,
            DeliveryMethods.IOS: self.mobile_format,
            DeliveryMethods.WEBAPP: self.webapp_format,
        }
        deep_link.url_templates.clear()
        for delivery_method, format in templates.items():
            template = DeepLinkUrlTemplate(
                delivery_method=delivery_method.model,
                link=deep_link,
                url_template=format,
            )
            template.save()


_links: list[DeepLinkDefinition] = []


class DeepLink(models.Model):
    name = models.CharField(max_length=64, primary_key=True)

    display_name = models.CharField(max_length=64)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    url_templates = models.ManyToManyField(DeliveryMethod, through='DeepLinkUrlTemplate')

    @classmethod
    def get_urls_from_global_id(cls, instance: Optional[Model]) -> dict[DeliveryMethod, str]:
        if instance is None:
            return {}
        content_type: ContentType = ContentType.objects.get_for_model(model=instance)
        global_id: str = instance.global_id
        deep_link: DeepLink = DeepLink.objects.filter(content_type=content_type).first()
        if deep_link is None:
            return {}
        url_templates: QuerySet[DeepLinkUrlTemplate] = DeepLinkUrlTemplate.objects.filter(
            link=deep_link
        )
        result: dict[DeliveryMethod, str] = {
            url_template.delivery_method: url_template.format(global_id=global_id)
            for url_template in url_templates
        }
        return result

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f'<{self.__class__.__name__}:{self.name}>'

    @staticmethod
    def register(webapp: str, mobile: str):
        def wrapper(cls):
            _links.append(DeepLinkDefinition(
                model=cls,
                webapp_format=webapp,
                mobile_format=mobile,
            ))
            return cls

        return wrapper

    @classmethod
    def app_contif_register(cls, app_config: AppConfig):
        try:
            DeepLink.objects.count()
        except DatabaseError:
            logger.error(f"Unable to {cls.__name__} for {app_config.label}")
            return
        for deep_link in _links:
            deep_link.register(app_config)


class DeepLinkUrlTemplate(models.Model):
    link = models.ForeignKey(to=DeepLink, on_delete=models.CASCADE)

    delivery_method = models.ForeignKey(to=DeliveryMethod, on_delete=models.CASCADE)

    url_template = models.CharField(max_length=1024)

    def format(self, global_id: str) -> str:
        return self.url_template % {"global_id": global_id}

    def __str__(self):
        return f'{self.link.name}+{self.delivery_method.name}'

    def __repr__(self):
        return f'{self.link.name}+{self.delivery_method.name}:{self.url_template}'
