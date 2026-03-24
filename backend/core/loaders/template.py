import logging
from typing import TYPE_CHECKING, Tuple

from django.conf import settings
from django.core import signals
from django.db import router
from django.template import Origin, TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.template.loaders.base import Loader as BaseLoader

from ..apps import CoreConfig

if TYPE_CHECKING:
    from ..models import TemplateModel

logger = logging.getLogger(__name__)


class TemplatesCache(object):
    """
    Template caching mechanism
    """

    _instance: "TemplatesCache" = None

    def __init__(self):
        logger.debug("Initializing TemplatesCache")
        self.cache = self.get_cache_backend()

    def __new__(cls, *args, **kwargs):
        # Singleton Pattern here!
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    @classmethod
    def get_cache_backend(cls):
        """
        Compatibility wrapper for getting Django's cache backend instance
        """
        from django.core.cache import caches
        logger.debug(f"Getting cached from {settings.TEMPLATES_CACHE_BACKEND}")
        cache = caches.create_connection(settings.TEMPLATES_CACHE_BACKEND)
        logger.debug(f"Getting created form {settings.TEMPLATES_CACHE_BACKEND}")
        # Some caches -- python-memcached in particular -- need to do a cleanup at
        # the end of a request cycle. If not implemented in a particular backend
        # cache.close is a no-op
        signals.request_finished.connect(cache.close)
        return cache

    @classmethod
    def get_cache_key(cls, name: str):
        """
        Gets cache key for the given name.
        """
        return f"{cls.__name__}::{slugify(name)}"

    @classmethod
    def get_cache_notfound_key(cls, name: str):
        """
        Gets cache key for the given name indicating that it is not found.
        """
        return cls.get_cache_key(name) + "::notfound"

    def remove_notfound_key(self, instance: "TemplateModel"):
        """
        Remove notfound key as soon as we save the template.
        """
        try:
            key: str = self.get_cache_notfound_key(instance.name)
            self.cache.delete(key)
        except Exception:
            if settings.IS_DEV:
                logger.warning(f'Could not remove notfound key {instance.name} from cache')
            else:
                logger.exception(f'Could not remove notfound key {instance.name} from cache')

    def set_and_return(self, cache_key: str, content: str, display_name: str) -> Tuple[str, str]:
        """
        Save in cache backend explicitly if manually deleted or invalidated
        """
        if self.cache:
            try:
                self.cache.set(cache_key, content)
            except Exception as e:
                if settings.IS_DEV:
                    logger.warning(f'Could not set template {cache_key} to cache: {e}')
                else:
                    logger.exception(f'Could not set template {cache_key} to cache: {e}')

        return content, display_name

    def add_template_to_cache(self, instance: "TemplateModel", **kwargs):
        """
        Called via Django's signals to cache the templates, if the template
        in the database was added or changed.
        """
        try:
            self.remove_cached_template(instance)
            self.remove_notfound_key(instance)
            key: str = self.get_cache_key(instance.name)
            logger.debug(f'Adding template {key} to cache')
            self.cache.set(key, instance.content)
        except Exception as e:
            if settings.IS_DEV:
                logger.warning(f'Could not add template {instance.name} to cache: {e}')
            else:
                logger.exception(f'Could not add template {instance.name} to cache: {e}')

    def remove_cached_template(self, instance: "TemplateModel", **kwargs):
        """
        Called via Django's signals to remove cached templates, if the template
        in the database was changed or deleted.
        """
        try:
            key: str = self.get_cache_key(instance.name)
            logger.debug(f'Removing template {key} from cache')
            self.cache.delete(key)
        except Exception:
            if settings.IS_DEV:
                logger.warning(f'Could not remove template {instance.name} from cache')
            else:
                logger.exception(f'Could not remove template {instance.name} from cache')


class Loader(BaseLoader):
    """
    A custom template loader to load templates from the database.
    """
    is_usable = True
    _templates = {}

    @property
    def cache(self) -> TemplatesCache:
        """
        Returns the cache template
        """
        return TemplatesCache()

    def _load_templates(self):
        from ..models import TemplateModel
        if not self._templates:
            for template in TemplateModel.objects.all():
                logger.debug(f'Loading template {template.name}')
                self.cache.add_template_to_cache(template)
                self._templates[template.name] = Origin(
                    name=template.name,
                    template_name=template.name,
                    loader=self,
                )

    def get_template_sources(self, template_name, template_dirs=None):
        self._load_templates()
        if template_name in self._templates:
            yield self._templates[template_name]

    def get_contents(self, origin):
        content, _ = self._load_template_source(origin.template_name)
        return content

    def _load_and_store_template(
            self,
            template_name: str,
            cache_key: str,
            **params):
        from ..models import TemplateModel
        template = TemplateModel.objects.get(name__exact=template_name, **params)
        db = router.db_for_read(TemplateModel, instance=template)
        display_name = f'{CoreConfig.name}:{db}:{template_name}'
        return self.cache.set_and_return(cache_key, template.content, display_name)

    def _load_template_source(self, template_name: str, template_dirs=None):
        # The logic should work like this:
        # * Try to find the template in the cache. If found, return it.
        # * Now check the cache if a lookup for the given template
        #   has failed lately and hand over control to the next template
        #   loader waiting in line.
        # * If this still did not fail we first try to find a site-specific
        #   template in the database.
        # * On a failure from our last attempt we try to load the global
        #   template from the database.
        # * If all of the above steps have failed we generate a new key
        #   in the cache indicating that queries failed, with the current
        #   timestamp.
        cache_key = self.cache.get_cache_key(template_name)

        try:
            backend_template = self.cache.get(cache_key)
            if backend_template:
                return backend_template, template_name
        except Exception:
            logger.debug(f'{cache_key} not found on cache')

        # Not found in cache, move on.
        cache_notfound_key = self.cache.get_cache_notfound_key(template_name)
        try:
            notfound = self.cache.get(cache_notfound_key)
            if notfound:
                raise TemplateDoesNotExist(template_name)
        except Exception:
            logger.debug(f'{cache_notfound_key} not found on cache')

        # Not marked as not-found, move on...

        from ..models import TemplateModel
        try:
            return self._load_and_store_template(
                template_name,
                cache_key,
            )
        except (TemplateModel.MultipleObjectsReturned, TemplateModel.DoesNotExist):
            try:
                return self._load_and_store_template(
                    template_name,
                    cache_key
                )
            except (TemplateModel.MultipleObjectsReturned, TemplateModel.DoesNotExist):
                pass

        # Mark as not-found in cache.
        self.cache.set_and_return(cache_notfound_key, '1', cache_notfound_key)
        raise TemplateDoesNotExist(template_name)
