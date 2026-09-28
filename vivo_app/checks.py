"""
Reports explicit page-data configuration during Django startup checks.
"""

from django.core.checks import CheckMessage, Error, Info, register

from vivo_app.lib.page_data import get_bundle, selected_mode
from vivo_app.lib.prepared_data import PageDataError


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
            detail = 'search and person profiles use source processing; other page families remain unavailable'
        messages.append(Info(f'Page data mode: {mode}; {detail}.', id='vivo_app.I001'))
    except PageDataError as exc:
        messages.append(Error(str(exc), id='vivo_app.E001'))
    return messages
