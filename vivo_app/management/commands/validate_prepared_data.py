"""
Checks a complete external prepared-data bundle without network access.
"""

import json
from pathlib import Path
from typing import ClassVar

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from vivo_app.lib.prepared_data import PageDataError, load_bundle


class Command(BaseCommand):
    """Validates every included file and reports data origin and coverage."""

    help = 'Validate prepared pages, responses, assets, and cases; never contacts services.'
    requires_system_checks: ClassVar[list[str]] = []

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Accepts an optional directory and selected cases to require.

        Called by: Django management command runner
        """
        parser.add_argument('directory', nargs='?', default=settings.PREPARED_FIXTURE_DIR)
        parser.add_argument('--case', action='append', default=[], dest='cases')

    def handle(self, *args: object, **options: object) -> None:
        """
        Validates files and prints a machine-readable aggregate report.

        Called by: Django management command runner
        """
        directory = Path(str(options['directory']))
        if not directory.is_absolute():
            directory = Path(settings.BASE_DIR) / directory
        try:
            bundle = load_bundle(directory)
            selected = options.get('cases')
            if isinstance(selected, list) and any(case not in bundle.cases for case in selected):
                raise PageDataError('A required case is absent from the prepared bundle.')
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        report = {
            'status': 'valid',
            'bundle_version': bundle.version,
            'data_origin': bundle.origin,
            'prepared_at': bundle.prepared_at,
            'application_revision': bundle.application_revision,
            'cases': len(bundle.cases),
            'entries': len(bundle.entries),
            'assets': len(bundle.assets),
            'source_integration': 'not_verified',
            'visual_equivalence': 'not_verified',
        }
        self.stdout.write(json.dumps(report, indent=2))
