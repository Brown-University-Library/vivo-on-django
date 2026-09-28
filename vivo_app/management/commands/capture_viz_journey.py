"""
Exposes a bounded visualization-service capture as a Django command.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tools.viz_capture import capture_visualizations
from vivo_app.lib.prepared_data import PageDataError


class Command(BaseCommand):
    """Captures selected public graph inputs for exact local replay."""

    help = 'Capture one person and optional ordinary organization graph family outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds selected record identifiers and a new external directory.

        Called by: Django management command runner
        """
        parser.add_argument('--person-id', required=True)
        parser.add_argument('--organization-id')
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Captures the service responses and verifies offline replay.

        Called by: Django management command runner
        """
        person_id, organization_id, output = options['person_id'], options.get('organization_id'), options['output']
        if not isinstance(person_id, str) or not isinstance(output, Path):
            raise CommandError('A person identifier and new output directory are required.')
        if organization_id is not None and not isinstance(organization_id, str):
            raise CommandError('The organization identifier must be text.')
        try:
            count = capture_visualizations(person_id, organization_id, output)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured and replayed {count} visualization responses.')
