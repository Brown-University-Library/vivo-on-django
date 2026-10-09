# Retired conversion code

These reference files came from revision `8c5c8ce`. Their original paths are preserved below, with `.txt` added so application imports, Django command discovery, and test discovery cannot execute them. Use the source revision in a separate checkout to reproduce the original setup.

| Original source | What it did |
| --- | --- |
| [tools/source_capture.py](tools/source_capture.py.txt) | Gathered a limited set of searches, profiles, organizations, images, documents, books, and custom graph inputs for exact replay. |
| [tools/viz_capture.py](tools/viz_capture.py.txt) | Gathered ordinary graph lists/responses and compared their parsed live/replay results. |
| [tools/validate_recordings.py](tools/validate_recordings.py.txt) | Checked selected saved-response cases without contacting services. |
| Capture command files under `vivo_app/management/commands/` | Supplied Django entry points for the retired capture helpers. |
| [vivo_app/lib/visualization.py](vivo_app/lib/visualization.py.txt) | Supplied standalone sample network, timeline, and organization visualization classes. |
| [test_visualization.py](test_visualization.py.txt) | Checked those sample classes and export helpers. |
| `test_excerpts/` | Preserves the seven retired capture/validator tests and one helper; complete originals remain in the outer archive. |

The maintained [comparison tool](../../tools/tools_readme.md) remains active. Current graph/chart processing and live source readers remain in `vivo_app/lib/`.
