from django.apps import AppConfig


class CoreUiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_ui'

    def ready(self):
        # Register core_ui processors
        self._register_processors()

    @staticmethod
    def _register_processors():
        """Register core_ui data processors."""
        from core.models.process import EntityType
        from core.utils.processor_registry import register_processor
        from core_ui.utils.file_processor.components_processor import ComponentsProcessor

        register_processor(EntityType.COMPONENTS, ComponentsProcessor)
