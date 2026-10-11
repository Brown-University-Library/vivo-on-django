"""
Supplies application page data from configured sources.
"""

from django.conf import settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_books import homepage_books
from vivo_app.lib.source_pages import organization_data, profile_data, search_data
from vivo_app.lib.source_teams import custom_organization_members, team_data


def check_source_configuration() -> None:
    """
    Checks required source configuration without contacting services.

    Called by: checks.check_page_data(), middleware.SourceDataMiddleware.__call__(), check_dev_sources.Command.handle()
    """
    if not settings.SOLR_URL:
        raise PageDataError('Search and profiles require SOLR_URL.')


def get_search_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies search results and navigation from Solr.

    Called by: views.search()
    """
    return search_data(query)


def get_profile_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies a person profile with its optional sections.

    Called by: views.display_show()
    """
    if query:
        raise PageDataError('Profile query options are not connected to source data yet.')
    return profile_data(path.rstrip('/').rsplit('/', 1)[-1])


def get_organization_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies an organization or team with its ordered members.

    Called by: views.display_show()
    """
    if query:
        raise PageDataError('Organization query options are not connected to source data yet.')
    identifier = path.rstrip('/').rsplit('/', 1)[-1]
    if identifier.startswith('team-'):
        result = team_data(identifier)
    else:
        result = organization_data(identifier, extra_member_ids=custom_organization_members(identifier))
    return result


def get_home_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies homepage books and background choices.

    Called by: views.home_index()
    """
    if path != '/' or query:
        raise PageDataError('The requested homepage variation is unsupported.')
    return homepage_books()
