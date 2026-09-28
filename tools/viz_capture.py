"""
Captures selected production visualization inputs and checks exact offline replay.
"""

import time
from pathlib import Path

from django.test import override_settings

from tools.source_capture import CapturingReader, write_capture
from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_graph import visualization_graph, visualization_key, visualization_list
from vivo_app.lib.source_teams import CUSTOM_ORGANIZATION_IDS


def capture_visualizations(person_id: str, organization_id: str | None, output: Path) -> int:
    """
    Saves selected service responses, then verifies them through the normal replay reader.

    Called by: management.commands.capture_viz_journey.Command.handle()
    """
    visualization_key('coauthors', person_id)
    if organization_id is not None:
        visualization_key('collaborators', organization_id)
        if organization_id.startswith('team-') or organization_id in CUSTOM_ORGANIZATION_IDS:
            raise PageDataError('Custom collaboration graphs use Solr member records, not the visualization service.')
    reader = CapturingReader()
    coauthor_list = visualization_list('coauthors', 'live', reader)
    time.sleep(0.5)
    collaborator_list = visualization_list('collaborators', 'live', reader)
    time.sleep(0.5)
    coauthor = visualization_graph('coauthors', person_id, 'live', reader)
    time.sleep(0.5)
    collaboration = visualization_graph('collaborators', person_id, 'live', reader)
    organization = None
    if organization_id is not None:
        time.sleep(0.5)
        organization = visualization_graph('collaborators', organization_id, 'live', reader)
    write_capture(output, reader.responses, 'visualization')
    with override_settings(
        UPSTREAM_RECORDING_MANIFEST=str(output / 'manifest.json'), UPSTREAM_RECORDING_CASE='visualization'
    ):
        if coauthor_list != visualization_list('coauthors', 'replay'):
            raise PageDataError('The coauthor availability list changed during replay.')
        if collaborator_list != visualization_list('collaborators', 'replay'):
            raise PageDataError('The collaborator availability list changed during replay.')
        if coauthor != visualization_graph('coauthors', person_id, 'replay'):
            raise PageDataError('The coauthor graph changed during replay.')
        if collaboration != visualization_graph('collaborators', person_id, 'replay'):
            raise PageDataError('The collaborator graph changed during replay.')
        if organization_id is not None and organization != visualization_graph('collaborators', organization_id, 'replay'):
            raise PageDataError('The organization collaboration graph changed during replay.')
    return len(reader.responses)
