"""
Exposes a bounded original-representation capture as a Django command.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tools.source_capture import capture_vivo_exports
from vivo_app.lib.prepared_data import PageDataError


class Command(BaseCommand):
    """Captures one record's JSON-LD, Turtle, and RDF outside Git."""

    help = 'Capture three VIVO representations for exact local replay outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds one record identifier and a new external output directory.

        Called by: Django management command runner
        """
        parser.add_argument('--id', required=True)
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Captures three live representations after validating command inputs.

        Called by: Django management command runner
        """
        identifier, output = options['id'], options['output']
        if not isinstance(identifier, str) or not isinstance(output, Path):
            raise CommandError('A record identifier and output directory are required.')
        try:
            count = capture_vivo_exports(identifier, output)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured {count} representations for one replay case.')
