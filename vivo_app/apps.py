from django.apps import AppConfig


class VivoAppConfig(AppConfig):
    name = 'vivo_app'

    def ready(self) -> None:
        """
        Registers page-data startup checks.

        Called by: Django application setup
        """
        from vivo_app import checks

        # Importing checks registers the decorated check with Django.
