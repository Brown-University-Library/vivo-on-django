"""
Runs Django tests for vivo-on-django.

Usage examples:
    (all) uv run ./run_tests.py
    (app) uv run ./run_tests.py vivo_app
    (module) uv run ./run_tests.py vivo_app.tests.test_home
    (class) uv run ./run_tests.py vivo_app.tests.test_home.HomePageTests
    (method) uv run ./run_tests.py vivo_app.tests.test_home.HomePageTests.test_homepage_renders_ok

Also takes a -v or --verbose flag to show each test's name, docstring, and result.

Uses config.settings unless DJANGO_SETTINGS_MODULE is already set. The runner
selects prototype page data and local static URLs before Django loads the
private .env. This gives the suite a consistent baseline. Individual tests
override the mode when they check prepared, replay, live, or invalid modes.
Django creates and destroys a test database when needed.
"""

import argparse
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def build_parser() -> argparse.ArgumentParser:
    """
    Builds the command-line parser for the test runner.

    Called by: main()
    """
    parser = argparse.ArgumentParser(description='Run Django tests for vivo-on-django.')
    parser.add_argument(
        'test_label',
        nargs='?',
        default='.',
        help='Optional Django app, module, class, method, or discovery directory; defaults to all tests.',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Increase verbosity to level 2.',
    )
    return parser


def normalize_test_label(test_label: str) -> str:
    """
    Normalizes a dotted test label and aliases for all tests.

    Called by: run_tests()
    """
    normalized_label: str = test_label.removesuffix('.py')
    if normalized_label in {'tests', 'test', '.'}:
        normalized_label = '.'
    return normalized_label


def configure_test_environment() -> None:
    """
    Selects the page-data and static URL baseline used by the complete test suite.

    Called by: run_tests()
    """
    os.environ['PAGE_DATA_MODE'] = 'prototype'
    os.environ['STATIC_URL'] = '/static/'


def run_tests(test_label: str, verbose: bool) -> int:
    """
    Initializes Django and runs the selected tests without interactive prompts.

    Called by: main()
    """
    configure_test_environment()
    settings_module: str = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    test_labels: list[str] = [normalize_test_label(test_label)]
    verbosity: int = 2 if verbose else 1
    print(f'using settings-module, ``{settings_module}``', flush=True)
    django.setup()
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class(verbosity=verbosity, interactive=False)
    failures: int = test_runner.run_tests(test_labels)
    return failures


def main() -> None:
    """
    Parses arguments and exits with a failure status when any test fails.

    Called by: __main__
    """
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()
    failures: int = run_tests(args.test_label, args.verbose)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
