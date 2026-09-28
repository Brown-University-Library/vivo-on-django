"""
Exposes one read-only homepage book capture as a Django command.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tools.source_capture import capture_homepage_books
from vivo_app.lib.prepared_data import PageDataError


class Command(BaseCommand):
    """Captures active homepage book rows outside Git."""

    help = 'Capture active homepage book rows for exact local replay outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds a new external output directory.

        Called by: Django management command runner
        """
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Captures the configured read-only source and reports its response count.

        Called by: Django management command runner
        """
        output = options['output']
        if not isinstance(output, Path):
            raise CommandError('An output directory is required.')
        try:
            count = capture_homepage_books(output)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured {count} homepage book response for one replay case.')
