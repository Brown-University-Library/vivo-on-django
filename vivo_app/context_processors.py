"""Template context processors for project-wide variables."""
from __future__ import annotations
from urllib.parse import quote

from django.conf import settings
from django.http import HttpRequest


def vivo_globals(request: HttpRequest) -> dict[str, object]:
    """Return site-wide URLs and configuration values for templates."""
    manager_url: str = getattr(settings, "MANAGER_URL", "") or ""
    analytics_key: str = getattr(settings, "GOOGLE_ANALYTICS_KEY", "") or ""
    notice_banner_value: str = getattr(settings, "NOTICE_BANNER", "") or ""
    contact_template: str = getattr(settings, "CONTACT_US_URL_TEMPLATE", "") or ""

    page_link: str = ""
    if request is not None:
        page_link = quote(request.build_absolute_uri() or '')

    contact_us_url: str = contact_template.replace("{LINK}", page_link) if contact_template else ""

    local_page_data = settings.PAGE_DATA_MODE in {'prepared', 'replay'}
    context: dict[str, object] = {
        "manager_url": manager_url,
        "google_analytics_key": '' if local_page_data else analytics_key,
        "local_page_data": local_page_data,
        "notice_banner": notice_banner_value,
        "contact_us_url": contact_us_url,
    }
    return context
