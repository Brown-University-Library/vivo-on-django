"""
Builds active team pages from an external record of Rails-defined members.
"""

import json
import re
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static
from django.utils.html import escape

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordingError, external_path
from vivo_app.lib.source_pages import (
    SourceReader,
    documents,
    first_text,
    record_data,
    record_id,
    response_object,
    thumbnail_url,
)
from vivo_app.lib.source_requests import community_research_members_key, read_source, team_member_key

CUSTOM_ORGANIZATION_IDS = {'org-brown-univ-dept124', 'org-brown-univ-dept148'}


def source_definitions() -> dict[str, object]:
    """
    Reads code-defined membership details from a file outside Git.

    Called by: team_definition(), custom_organization_members()
    """
    raw_path = settings.TEAM_SOURCE_MANIFEST
    if not raw_path:
        raise PageDataError('The member source manifest is not configured.')
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    try:
        value: object = json.loads(external_path(path).read_text())
    except (OSError, ValueError, RecordingError) as exc:
        raise PageDataError('The member source manifest is unavailable or invalid.') from exc
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise PageDataError('The member source manifest is invalid.')
    return value


def custom_organization_members(identifier: str, mode: str, reader: SourceReader | None = None) -> list[str]:
    """
    Reads added member IDs for a scoped custom organization.

    Called by: page_data.get_organization_data(), tools.source_capture.capture_journey(), tests
    """
    if identifier not in CUSTOM_ORGANIZATION_IDS:
        return []
    if reader is None:
        reader = read_source
    definitions = source_definitions()
    organizations = definitions.get('organizations')
    entry = organizations.get(identifier) if isinstance(organizations, dict) else None
    members = entry.get('extra_member_ids') if isinstance(entry, dict) else None
    if (
        not isinstance(members, list)
        or len(members) > 100
        or any(not isinstance(member, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,80}', member) is None for member in members)
    ):
        raise PageDataError('The custom-organization member definition is missing or invalid.')
    if len(set(members)) != len(members):
        raise PageDataError('The custom-organization member list contains duplicates.')
    result = list(members)
    if identifier == 'org-brown-univ-dept148':
        response = response_object(community_research_members_key(), mode, reader)
        docs, total = documents(response)
        if total != len(docs):
            raise PageDataError('The research-area member query exceeded its response limit.')
        for doc in docs:
            if first_text(doc.get('record_type')) != 'PEOPLE':
                raise PageDataError('Solr returned an unrelated research-area member.')
            result.append(record_id(doc))
    return list(dict.fromkeys(result))


def team_definition(identifier: str) -> tuple[str, list[str]]:
    """
    Reads a scoped team name and member IDs from a file outside Git.

    Called by: team_data(), tests
    """
    teams = source_definitions().get('teams')
    team = teams.get(identifier) if isinstance(teams, dict) else None
    if not isinstance(team, dict):
        raise PageDataError('The requested active team is not configured.')
    name, members = team.get('name'), team.get('member_ids')
    if not isinstance(name, str) or not name or not isinstance(members, list):
        raise PageDataError('The active-team source definition is invalid.')
    if (
        not members
        or len(members) > 100
        or any(not isinstance(member, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,80}', member) is None for member in members)
    ):
        raise PageDataError('The active-team member list is invalid.')
    if len(set(members)) != len(members):
        raise PageDataError('The active-team member list contains duplicates.')
    return name, members


def team_data(identifier: str, mode: str, reader: SourceReader | None = None) -> dict[str, object]:
    """
    Builds the selected active-team organization page from Solr member records.

    Called by: page_data.get_organization_data(), tools.source_capture.capture_journey(), tests
    """
    if reader is None:
        reader = read_source
    name, member_ids = team_definition(identifier)
    response = response_object(team_member_key(member_ids), mode, reader)
    docs, _ = documents(response)
    members: dict[str, dict[str, object]] = {}
    for doc in docs:
        member_id = record_id(doc)
        if member_id not in member_ids or first_text(doc.get('record_type')) != 'PEOPLE' or member_id in members:
            raise PageDataError('Solr returned an unrelated active-team member.')
        members[member_id] = doc
    if set(members) != set(member_ids):
        raise PageDataError('Solr did not return every active-team member.')
    faculty: list[dict[str, str]] = []
    for doc in docs:
        member_id = record_id(doc)
        item = record_data(doc)
        faculty.append(
            {
                'name': first_text(doc.get('display_name_s')) or first_text(item.get('name')),
                'title': first_text(item.get('title')),
                'url': '/display/' + member_id,
                'image': thumbnail_url(doc),
            }
        )
    return {
        'id': identifier,
        'name': name,
        'page_title': name,
        'image': static('images/org_placeholder_noborder.png'),
        'website_links': [],
        'overview_html': '<p>' + escape(name) + '</p>',
        'visualization_url': '',
        'administrative_positions': [],
        'faculty_positions': faculty,
    }
