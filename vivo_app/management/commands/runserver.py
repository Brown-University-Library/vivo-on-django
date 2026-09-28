"""
Explains missing local page assets when runserver does not serve static files.
"""

from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.contrib.staticfiles.management.commands.runserver import Command as StaticRunserverCommand
from django.core.handlers.wsgi import WSGIHandler


class Command(StaticRunserverCommand):
    """Retains Django's runserver behavior and adds a local preview diagnostic."""

    def get_handler(self, *args: object, **options: object) -> StaticFilesHandler | WSGIHandler:
        """
        Warns when this development server will omit page styles, scripts, and images.

        Called by: Django runserver inner_run()
        """
        handler = super().get_handler(*args, **options)
        if not options.get('use_static_handler'):
            detail = 'The --nostatic option disables static files. Omit it for a styled local preview.'
        elif not settings.DEBUG and not options.get('insecure_serving'):
            detail = (
                'DEBUG=False disables static files in ordinary runserver. '
                'For local preview, set DJANGO_DEBUG=True in your local environment, '
                'then stop and restart runserver. To test locally with DEBUG=False, use runserver --insecure.'
            )
        else:
            detail = ''
        if detail:
            self.stderr.write(
                'Local preview: this runserver will not serve CSS, JavaScript, logos, or icons. '
                f'Pages will look unstyled unless another server supplies those files. {detail}'
            )
        return handler
