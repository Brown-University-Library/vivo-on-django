"""
Supplies page-family data through explicitly selected local modes.
"""

from functools import lru_cache
from pathlib import Path

from django.conf import settings

from vivo_app.lib.prepared_data import PageDataError, PreparedBundle, PreparedEntry, load_bundle


def selected_mode() -> str:
    """
    Rejects unknown modes and missing source settings without contacting them.

    Called by: get_bundle(), checks.check_page_data()
    """
    mode: str = settings.PAGE_DATA_MODE
    if mode not in {'prototype', 'prepared', 'replay', 'live'}:
        raise PageDataError('PAGE_DATA_MODE must be prototype, prepared, replay, or live.')
    if mode == 'live' and not settings.SOLR_URL:
        raise PageDataError('Live search and profiles require SOLR_URL.')
    if mode == 'replay' and not settings.UPSTREAM_RECORDING_MANIFEST:
        raise PageDataError('Replay search and profiles require UPSTREAM_RECORDING_MANIFEST.')
    return mode


@lru_cache(maxsize=4)
def cached_bundle(directory: str) -> PreparedBundle:
    """
    Loads an immutable bundle once per process; a new version requires a restart.

    Called by: get_bundle()
    """
    return load_bundle(Path(directory))


def get_bundle() -> PreparedBundle | None:
    """
    Loads the explicitly selected prepared bundle or retains explicit prototype mode.

    Called by: get_search_data(), get_profile_data(), get_response_data(), views.prepared_asset()
    """
    result = None
    if selected_mode() == 'prepared':
        directory = Path(settings.PREPARED_FIXTURE_DIR)
        if not directory.is_absolute():
            directory = Path(settings.BASE_DIR) / directory
        result = cached_bundle(str(directory.resolve()))
    return result


def get_search_data(path: str, query: list[tuple[str, str]]) -> dict[str, object] | None:
    """
    Supplies an exact search state without implementing a local search engine.

    Called by: views.search()
    """
    bundle = get_bundle()
    result = None
    if bundle is not None:
        result = dict(bundle.page('search', path, query).data)
        page, page_size, total = result['page'], result['page_size'], result['total']
        if isinstance(page, int) and isinstance(page_size, int) and isinstance(total, int):
            result['start'] = (page - 1) * page_size + 1
            result['end'] = min(page * page_size, total)
    elif selected_mode() in {'live', 'replay'}:
        from vivo_app.lib.source_pages import search_data

        result = search_data(query, selected_mode())
    return result


def get_profile_data(path: str, query: list[tuple[str, str]]) -> dict[str, object] | None:
    """
    Supplies a profile with its recorded optional sections and explicit identity.

    Called by: views.display_show()
    """
    bundle = get_bundle()
    result = None if bundle is None else dict(bundle.page('profile', path, query).data)
    if bundle is None and selected_mode() in {'live', 'replay'}:
        if query:
            raise PageDataError('Profile query options are not connected to source data yet.')
        from vivo_app.lib.source_pages import profile_data

        result = profile_data(path.rstrip('/').rsplit('/', 1)[-1], selected_mode())
    return result


def get_organization_data(path: str, query: list[tuple[str, str]]) -> dict[str, object] | None:
    """
    Supplies one exact organization page with its ordered member roles.

    Called by: views.display_show()
    """
    bundle = get_bundle()
    result = None if bundle is None else dict(bundle.page('organization', path, query).data)
    if bundle is None and selected_mode() in {'live', 'replay'}:
        if query:
            raise PageDataError('Organization query options are not connected to source data yet.')
        identifier = path.rstrip('/').rsplit('/', 1)[-1]
        if identifier.startswith('team-'):
            from vivo_app.lib.source_teams import team_data

            result = team_data(identifier, selected_mode())
        else:
            from vivo_app.lib.source_pages import organization_data
            from vivo_app.lib.source_teams import custom_organization_members

            result = organization_data(
                identifier, selected_mode(), extra_member_ids=custom_organization_members(identifier, selected_mode())
            )
    return result


def get_home_data(path: str, query: list[tuple[str, str]]) -> dict[str, object] | None:
    """
    Supplies the observed homepage book order and background choices.

    Called by: views.home_index()
    """
    bundle = get_bundle()
    result = None if bundle is None else dict(bundle.page('home', path, query).data)
    if bundle is None and selected_mode() in {'live', 'replay'}:
        raise PageDataError('The homepage is not connected to source data yet.')
    return result


def get_response_data(path: str, query: list[tuple[str, str]]) -> PreparedEntry | None:
    """
    Supplies original bytes for saved JSON, download, or redirect responses.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    bundle = get_bundle()
    result = None if bundle is None else bundle.page('response', path, query)
    if bundle is None and selected_mode() in {'live', 'replay'}:
        raise PageDataError('This response format is not connected to source data yet.')
    return result
