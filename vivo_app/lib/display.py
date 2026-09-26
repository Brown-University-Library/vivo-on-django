"""
Display helpers and data-prep for the Django VIVO app.

This module mirrors the Rails DisplayController responsibilities at a high level,
using a lightweight mock strategy for offline development.
"""

from typing import Any


def get_type_for_id(entity_id: str) -> str | None:
    """Best-effort type detection for an entity id.

    Offline heuristic (no SOLR):
    - IDs starting with 'n' are treated as PEOPLE
    - IDs starting with 'org' or 'o' are treated as ORGANIZATION
    - IDs starting with 'team' are treated as TEAM
    - Otherwise, unknown (None)
    """
    if not entity_id:
        return None
    lid = entity_id.lower()
    if lid.startswith('n'):
        return 'PEOPLE'
    if lid.startswith(('org', 'o')):
        return 'ORGANIZATION'
    if lid.startswith('team'):
        return 'TEAM'
    return None


def build_display_context(entity_id: str, entity_type: str | None, request) -> dict[str, Any]:
    """Build a minimal context dict for rendering or JSON output.

    Mirrors key fields used by Rails templates/presenters at a minimal level
    so we can progressively enhance later.
    """
    context: dict[str, Any] = {
        'id': entity_id,
        'type': entity_type,
        'vivo_id': entity_id,
    }

    # Presenter-like structures (very minimal for parity scaffolding)
    if entity_type == 'PEOPLE':
        context['presenter'] = {
            'faculty': {
                'vivo_id': entity_id,
                'id': entity_id,
                'name': f'Mock Person {entity_id}',
                'display_name': f'Mock Person {entity_id}',
                'title': 'Professor of Example Studies',
                'email': f'{entity_id}@example.edu',
                # Minimal HTML string to mirror Rails overview usage
                'overview': f'<p>Overview for Mock Person {entity_id}.</p>',
                'thumbnail': None,
                'hidden': False,
                'cv_link': None,
                # Collections used by various tabs/sections
                'affiliations': [],
                'research_areas': [],
                'on_the_web': [],
            },
            # Top-level presenter flags used for tab visibility and UI behavior
            'show_visualizations': request.GET.get('viz') == 'true',
            'has_coauthors': False,
            'has_collaborators': False,
            'show_back_to_search': True,
            'edit_mode': False,
            'can_edit': False,
            'edit_errors': [],
            # Tab presence flags (deterministic scaffolding)
            'has_publications': True,
            'has_research': False,
            'has_background': False,
            'has_affiliations': False,
            'has_teaching': False,
            'has_details': True,
        }
    elif entity_type in ('ORGANIZATION', 'TEAM'):
        context['presenter'] = {
            'organization': {
                'id': entity_id,
                'name': f'Mock Organization {entity_id}',
            },
            'show_visualizations': request.GET.get('viz') == 'true',
        }

    return context


def build_publications_context(entity_id: str, entity_type: str | None, request) -> dict[str, Any]:
    """Build minimal publications context.

    Uses the base display context and adds a publications list. This is a
    deterministic mock suitable for offline development and test parity.
    """
    context = build_display_context(entity_id, entity_type, request)

    # Minimal, deterministic mock publications
    pubs = []
    if entity_type in ('ORGANIZATION', 'PEOPLE', 'TEAM'):
        pubs = [
            {
                'id': f'{entity_id}-pub-1',
                'title': f'Sample Publication 1 for {entity_id}',
                'authors': [
                    context.get('presenter', {}).get('faculty', {}).get('name')
                    or context.get('presenter', {}).get('organization', {}).get('name')
                    or f'Contributor {entity_id}'
                ],
                'year': 2021,
                'type': 'Journal Article',
                'citation': 'Doe, J. (2021). Sample Article. Journal of Examples.',
            },
            {
                'id': f'{entity_id}-pub-2',
                'title': f'Sample Publication 2 for {entity_id}',
                'authors': ['Alice Example', 'Bob Example'],
                'year': 2020,
                'type': 'Conference Paper',
                'citation': 'Example, A., & Example, B. (2020). Conference Paper. Proc. Conf.',
            },
        ]
    context['publications'] = pubs
    return context
