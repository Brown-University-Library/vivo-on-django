from importlib import import_module

from django.apps import AppConfig


class VivoAppConfig(AppConfig):
    name = 'vivo_app'

    def ready(self) -> None:
        """
        Registers page-data startup checks.

        Called by: Django application setup
        """
        ## importing checks registers the decorated check with Django
        import_module('vivo_app.checks')
