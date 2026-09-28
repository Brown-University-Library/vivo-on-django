"""
Checks saved source responses without contacting a service.
"""

import argparse
from pathlib import Path

from vivo_app.lib.recorded_responses import RecordingError, load_recordings


def main() -> None:
    """
    Checks selected cases locally and reports whether their data is synthetic.

    Called by: __main__
    """
    parser = argparse.ArgumentParser(description='Validate saved GET responses; never contacts a service.')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--case', action='append', required=True, dest='cases')
    parser.add_argument('--require-recorded', action='store_true', help='Reject a manifest marked synthetic.')
    args = parser.parse_args()
    try:
        recordings = load_recordings(args.manifest)
        if args.require_recorded and recordings.data_kind != 'recorded':
            raise RecordingError('Authentic upstream recordings are still required; this manifest is synthetic.')
        counts = [len(recordings.for_case(case_id)) for case_id in args.cases]
    except RecordingError as exc:
        parser.exit(1, f'Recording check failed: {exc}\n')
    else:
        print(f'Validated {len(counts)} selected cases ({recordings.data_kind}); response counts: {counts}.')
        print('This checks saved files, not completeness of page inputs or agreement with the public site.')


if __name__ == '__main__':
    main()
