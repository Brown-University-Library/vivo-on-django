"""
Reports page-data configuration and checks collected files during deployment checks.
"""

from pathlib import Path

from django.conf import settings
from django.core.checks import CheckMessage, Error, Info, Tags, register

from vivo_app.lib.page_data import get_bundle, selected_mode
from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.static_assets import collected_asset_differences


@register()
def check_page_data(app_configs: object = None, **kwargs: object) -> list[CheckMessage]:
    """
    Validates the selected data mode without contacting services.

    Called by: Django system checks
    """
    messages: list[CheckMessage] = []
    try:
        mode = selected_mode()
        bundle = get_bundle()
        detail = 'sample content; no source integration'
        if bundle is not None:
            detail = f'bundle {bundle.version}; {bundle.origin}; {len(bundle.cases)} cases; no source integration'
        elif mode in {'live', 'replay'}:
            detail = 'search, person profiles, and ordinary organizations use source processing; other families remain unavailable'
        messages.append(Info(f'Page data mode: {mode}; {detail}.', id='vivo_app.I001'))
    except PageDataError as exc:
        messages.append(Error(str(exc), id='vivo_app.E001'))
    return messages


@register(Tags.staticfiles, deploy=True)
def check_static_collection(app_configs: object = None, **kwargs: object) -> list[CheckMessage]:
    """
    Checks application stylesheet and script copies without requesting or changing data.

    Called by: django.core.checks.registry.CheckRegistry.run_checks()
    """
    messages: list[CheckMessage] = []
    root = settings.STATIC_ROOT
    if not root:
        messages.append(Error('Set STATIC_ROOT before collecting application stylesheets and scripts.', id='vivo_app.E002'))
    else:
        try:
            differences = collected_asset_differences(Path(settings.BASE_DIR) / 'vivo_app' / 'static', Path(root))
            if differences:
                messages.append(
                    Error(
                        f'{len(differences)} collected application stylesheets or scripts are missing, unreadable, or stale.',
                        hint='Run uv run ./manage.py collectstatic --noinput, then repeat this check.',
                        id='vivo_app.E002',
                    )
                )
        except (OSError, ValueError):
            messages.append(Error('Application stylesheet and script source files cannot be checked.', id='vivo_app.E003'))
    return messages
