"""
Exposes a paced custom-graph source capture as a Django command.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tools.source_capture import capture_custom_graph
from vivo_app.lib.prepared_data import PageDataError


class Command(BaseCommand):
    """Captures one calculated graph's Solr inputs outside Git."""

    help = 'Capture a team or specialized-organization graph for exact replay outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds a custom graph identifier and new output directory.

        Called by: Django management command runner
        """
        parser.add_argument('--id', required=True)
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Captures one calculated graph and reports the response count.

        Called by: Django management command runner
        """
        identifier, output = options['id'], options['output']
        if not isinstance(identifier, str) or not isinstance(output, Path):
            raise CommandError('A graph identifier and output directory are required.')
        try:
            count = capture_custom_graph(identifier, output)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured {count} Solr responses for one custom graph replay case.')
