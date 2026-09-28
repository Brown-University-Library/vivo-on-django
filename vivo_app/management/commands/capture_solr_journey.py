"""
Exposes the development-only source capture as a Django command.
"""

from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tools.source_capture import capture_journey
from vivo_app.lib.prepared_data import PageDataError


class Command(BaseCommand):
    """Captures one bounded live journey for exact local replay."""

    help = 'Capture a search and person profile, optionally with an organization and extra search states, outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds one query, one profile identifier, and a new external directory.

        Called by: Django management command runner
        """
        parser.add_argument('--query', required=True)
        parser.add_argument('--id', required=True)
        parser.add_argument('--organization-id')
        parser.add_argument('--extra-search', action='append', default=[])
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Validates command arguments and starts one external capture.

        Called by: Django management command runner
        """
        query, identifier, output = options['query'], options['id'], options['output']
        organization_id = options.get('organization_id')
        extra_searches = options.get('extra_search')
        if not isinstance(query, str) or not isinstance(identifier, str) or not isinstance(output, Path):
            raise CommandError('Query, profile identifier, and output directory are required.')
        if organization_id is not None and not isinstance(organization_id, str):
            raise CommandError('The organization identifier must be text.')
        if (
            not isinstance(extra_searches, list)
            or len(extra_searches) > 4
            or any(not isinstance(value, str) or len(value) > 1000 for value in extra_searches)
        ):
            raise CommandError('Provide at most four short extra search query strings.')
        try:
            count = capture_journey(query, identifier, output, organization_id, extra_searches)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured {count} responses for one replay case.')
