"""
Exposes versioned stylesheet and script URLs to templates.
"""

from django import template

from vivo_app.lib.static_assets import versioned_asset_url

register = template.Library()


@register.simple_tag
def versioned_static(name: str) -> str:
    """
    Supplies a local asset URL with its content version.

    Called by: Django templates through the versioned_static tag
    """
    return versioned_asset_url(name)
