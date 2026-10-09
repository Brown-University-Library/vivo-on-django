"""
Checks visualization components using local sample data.

Usage:
    uv run -m unittest test_visualization -v
"""

import logging
import unittest

from vivo_app.lib.visualization import (
    NetworkVisualizer,
    OrganizationVisualizer,
    TimelineVisualizer,
    export_network_to_cytoscape,
    export_timeline_to_vis,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestVisualization(unittest.IsolatedAsyncioTestCase):
    """Checks sample visualization components without Django configuration."""

    def setUp(self) -> None:
        """
        Creates the sample visualizers for each test.

        Called by: unittest.TestCase.run()
        """
        self.network_viz = NetworkVisualizer()
        self.timeline_viz = TimelineVisualizer()
        self.org_viz = OrganizationVisualizer()

    async def test_network_visualizer(self) -> None:
        """
        Checks sample network data and its Cytoscape export.
        """
        logger.info('Testing network visualization...')

        # Test with a mock person URI
        person_uri = 'http://vivo.example.edu/individual/n1234'

        # This will use the mock implementation
        network = await self.network_viz.coauthorship_network(person_uri)

        # Check basic structure
        self.assertIn('nodes', network)
        self.assertIn('links', network)
        self.assertGreaterEqual(len(network['nodes']), 1)

        # Convert to Cytoscape format
        cyto_data = export_network_to_cytoscape(network)
        self.assertIn('elements', cyto_data)
        self.assertIn('nodes', cyto_data['elements'])
        self.assertIn('edges', cyto_data['elements'])

        logger.info('Network visualization test completed')

    async def test_timeline_visualizer(self) -> None:
        """
        Checks sample publication data and its timeline export.
        """
        logger.info('Testing timeline visualization...')

        # Test with a mock person URI
        person_uri = 'http://vivo.example.edu/individual/n1234'

        # This will use the mock implementation
        timeline = await self.timeline_viz.publication_timeline(person_uri)

        # Check basic structure
        self.assertIn('events', timeline)
        self.assertGreaterEqual(len(timeline['events']), 1)

        # Convert to vis.js format
        vis_data = export_timeline_to_vis(timeline)
        self.assertIn('items', vis_data)
        self.assertIn('groups', vis_data)

        logger.info('Timeline visualization test completed')

    async def test_organization_visualizer(self) -> None:
        """
        Checks the sample organization hierarchy.
        """
        logger.info('Testing organization visualization...')

        # Test with a mock organization URI
        org_uri = 'http://vivo.example.edu/individual/org123'

        # This will use the mock implementation
        org_chart = await self.org_viz.organization_chart(org_uri)

        # Check basic structure
        self.assertIn('name', org_chart)
        self.assertIn('type', org_chart)
        self.assertIn('children', org_chart)

        logger.info('Organization visualization test completed')


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
