# Checking saved upstream responses

The reader in [recorded_responses.py](../vivo_app/lib/recorded_responses.py) checks saved GET responses and returns their unchanged bytes. It never opens a network connection, writes files, or substitutes sample data for a missing recording. It is preparation for service integration; the current page helpers still use their existing prototype data.

Keep the manifest and all response bodies in a directory outside every Git checkout. The reader enforces that rule for synthetic examples too. It rejects missing files, changed checksums, duplicate requests, incomplete case references, and files that escape the recording directory. These checks establish file integrity, not that the data is authentic or that every dependency needed by a page has been saved.

Contents:

- [Run a local check](#run-a-local-check)
- [Manifest format](#manifest-format)
- [Use a saved response](#use-a-saved-response)
- [Remaining integration work](#remaining-integration-work)

## Run a local check

From the repository root, run:

```bash
uv run python -m vivo_app.lib.recorded_responses ../recordings/manifest.json --case SEARCH --case PROFILE --require-recorded
```

The command reads all entries in the manifest and validates their bodies, then checks the selected case names. It prints the declared data kind and response counts. It exits with a nonzero status for invalid or missing data. `--require-recorded` also rejects a manifest marked `synthetic`; it cannot verify the provenance of a file merely marked `recorded`. Omit that option only when deliberately checking invented examples during tool development.

## Manifest format

Use schema version `1`, a `data_kind` of `recorded` or `synthetic`, a `captured_at` timestamp including its timezone, a `recordings` array, and a `cases` object. Each case maps its identifier to a nonempty list of recording identifiers. Several cases can share a recording. Repeated reads of one request use the same response; a response that changes during a journey requires a separate capture set. This first reader does not model such sequences.

Each recording contains:

| Field | Required value |
| --- | --- |
| `id` | A unique recording identifier. |
| `request.service` | A service label, such as `solr`, without a server address. |
| `request.method` | `GET`. Other methods are not supported yet. |
| `request.path` | The service-relative path, starting with `/`, without a query string or fragment. |
| `request.query` | Decoded, ordered string pairs. Preserve every repeated key and blank value. |
| `request.headers` | Ordered string pairs for headers that affect the response; use `[]` if none apply. Do not store authentication or cookie headers. |
| `response.status` | The original HTTP status as an integer. Saved errors retain their error status. |
| `response.headers` | Ordered string pairs, including the original content type where provided. Keep only relevant response headers; omit cookies. |
| `response.body_file` | The filename relative to the manifest directory. |
| `response.sha256` | The lowercase SHA-256 checksum of the unchanged body bytes. |

Matching is deliberately exact. The service, path, ordered query pairs, and ordered header pairs must all agree, including header spelling. Changing pair order fails instead of silently assuming equivalent meaning. An HTTP client must decode query values once before constructing the key; a dictionary is unsuitable because it loses repeated keys.

## Use a saved response

```python
from pathlib import Path

from vivo_app.lib.recorded_responses import RequestKey, load_recordings

recordings = load_recordings(Path('../recordings/manifest.json'))
request = RequestKey('solr', '/select', (('q', 'sample topic'),))
response = recordings.get('SEARCH', request)
```

The example uses invented search text and requires an exactly matching entry in the external manifest. Inspect `response.status` and `response.headers` before treating its body as successful data. `response.json()` parses JSON and raises `RecordingError` for invalid JSON. Raw bytes remain available as `response.body` for other formats. HTTP errors are preserved as responses; the eventual service parser must apply the application's error behavior.

## Remaining integration work

Local template and interaction development can begin with prepared page data before authentic responses are available, as described in the [workplan](../PLAN__workplan.md#repeatable-data-for-local-development). That data is already arranged for rendering and will use a separate reader; do not present it as a raw upstream recording or weaken this reader's checks to accept it. Both approaches will supply the same documented fields to the same templates once response processing is connected. Prepared-data support remains to be implemented.

Obtain authentic requests and responses from the services that supply the selected search and profile. Include type detection, graph-availability lists when required, and the assets needed for the selected pages. Confirm the deployed request settings and align the capture date with the public reference. Public page JSON is not a substitute for an unchanged Solr response.

Then connect the selected recording set to the same parsing and data-preparation code that will consume live service responses. Live access must be explicitly selected and use `httpx2`; it must never serve as a fallback after a missing recording. This reader does not yet supply that live mode, Solr query execution, a capture command, or complete offline page rendering. Start with response replay; there is not yet evidence that a local Solr instance is necessary.

Run the reader's tests with `uv run ./run_tests.py vivo_app.tests.test_recorded_responses -v`. They create invented responses in a temporary directory outside the repository. No authentic record or publication content is included.
