"""
Provides sample co-authorship networks, organization charts, and publication timelines.

The visualizers return local sample data and do not contact external services.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VisualizationError(Exception):
    """Base exception for visualization errors."""


class NetworkVisualizer:
    """Handles network visualizations (co-authorship, collaboration, etc.)."""

    async def coauthorship_network(self, person_uri: str, depth: int = 1) -> dict[str, Any]:
        """
        Generate a co-authorship network for a person.

        Args:
            person_uri: URI of the person to build the network around
            depth: How many levels deep to explore the network

        Returns:
            Dictionary containing nodes and links for the network visualization
        """
        ## Returns sample data for the prototype.
        return {
            'nodes': [
                {'id': person_uri, 'label': 'Researcher', 'type': 'person'},
                {'id': 'coauthor1', 'label': 'Co-Author 1', 'type': 'person'},
                {'id': 'coauthor2', 'label': 'Co-Author 2', 'type': 'person'},
            ],
            'links': [
                {'source': person_uri, 'target': 'coauthor1', 'weight': 5},
                {'source': person_uri, 'target': 'coauthor2', 'weight': 3},
            ],
        }


class TimelineVisualizer:
    """Handles timeline visualizations for publications and other events."""

    async def publication_timeline(self, person_uri: str) -> dict[str, Any]:
        """
        Generate a timeline of publications for a person.

        Args:
            person_uri: URI of the person

        Returns:
            Dictionary containing timeline data for visualization
        """
        ## Returns sample data for the prototype.
        return {
            'events': [
                {
                    'year': 2023,
                    'publications': [
                        {'title': 'Sample Publication 1', 'type': 'Journal Article'},
                        {'title': 'Sample Publication 2', 'type': 'Conference Paper'},
                    ],
                },
                {
                    'year': 2022,
                    'publications': [
                        {'title': 'Older Publication', 'type': 'Journal Article'},
                    ],
                },
            ]
        }


class OrganizationVisualizer:
    """Handles organization charts and hierarchies."""

    async def organization_chart(self, org_uri: str) -> dict[str, Any]:
        """
        Generate an organization chart.

        Args:
            org_uri: URI of the organization

        Returns:
            Dictionary containing the organization hierarchy
        """
        ## Returns sample data for the prototype.
        return {
            'name': 'Sample Department',
            'type': 'AcademicDepartment',
            'children': [
                {
                    'name': 'Research Group 1',
                    'type': 'ResearchGroup',
                    'children': [
                        {'name': 'Researcher 1', 'type': 'Person'},
                        {'name': 'Researcher 2', 'type': 'Person'},
                    ],
                },
                {
                    'name': 'Research Group 2',
                    'type': 'ResearchGroup',
                    'children': [
                        {'name': 'Researcher 3', 'type': 'Person'},
                    ],
                },
            ],
        }


# Helper functions for common visualization tasks


def export_network_to_cytoscape(network_data: dict[str, Any]) -> dict[str, Any]:
    """Convert network data to Cytoscape.js format."""
    return {
        'elements': {
            'nodes': [{'data': {'id': node['id'], 'label': node['label']}} for node in network_data['nodes']],
            'edges': [
                {'data': {'source': link['source'], 'target': link['target'], 'weight': link.get('weight', 1)}}
                for link in network_data['links']
            ],
        }
    }


def export_timeline_to_vis(timeline_data: dict[str, Any]) -> dict[str, Any]:
    """Convert timeline data to vis.js timeline format."""
    items = []
    for event in timeline_data['events']:
        for pub in event['publications']:
            items.append(
                {
                    'id': f'pub{len(items)}',
                    'content': pub['title'],
                    'start': f'{event["year"]}-01-01',
                    'type': 'point',
                    'group': pub['type'],
                }
            )

    return {
        'items': items,
        'groups': [
            {'id': 'Journal Article', 'content': 'Journal Articles'},
            {'id': 'Conference Paper', 'content': 'Conference Papers'},
        ],
    }
