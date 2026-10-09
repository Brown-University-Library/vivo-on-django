# Checking saved upstream responses

The runtime reader in [recorded_responses.py](../vivo_app/lib/recorded_responses.py) checks saved GET responses and returns their unchanged bytes. It never opens a network connection, writes files, or substitutes sample data for a missing recording. Replay mode uses the reader to supply saved upstream responses to page processing. The reader and mode remain because live code shares their request/response helpers; see [code retained for review](code_retirement_review.md).

Keep the manifest and all response bodies in a directory outside every Git checkout. The reader enforces that rule for synthetic examples too. It rejects missing files, changed checksums, duplicate requests, incomplete case references, and files that escape the recording directory. These checks establish file integrity, not that the data is authentic or that every dependency needed by a page has been saved.

Contents:

- [Run a local check](#run-a-local-check)
- [Manifest format](#manifest-format)
- [Use a saved response](#use-a-saved-response)
- [Supported use](#supported-use)

## Run a local check

From the repository root, run:

```bash
uv run python - <<'PY'
from pathlib import Path
from vivo_app.lib.recorded_responses import load_recordings

recordings = load_recordings(Path('../recordings/manifest.json'))
if recordings.data_kind != 'recorded':
    raise ValueError('Replay mode requires a manifest marked recorded.')
print('SEARCH responses:', len(recordings.for_case('SEARCH')))
print('PROFILE responses:', len(recordings.for_case('PROFILE')))
PY
```

Replace the path and case names with those in your external manifest. This check reads all entries and validates their bodies, then checks the selected case names. It prints response counts and exits with a nonzero status for invalid or missing data. It contacts no service and changes no files. A manifest marked `recorded` still needs a trustworthy source; the label alone does not prove where its content came from.

## Manifest format

Use schema version `1`, a `data_kind` of `recorded` or `synthetic`, a `captured_at` timestamp including its timezone, a `recordings` array, and a `cases` object. Each case maps its identifier to a nonempty list of recording identifiers. Several cases can share a recording. Repeated reads of one request use the same response; a response that changes during a journey requires a separate capture set. The reader does not model such sequences.

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

## Supported use

Prepared page data contains already-arranged fields for local layout and interaction work. It is separate from raw upstream recordings. Search, profiles, organizations, facets, graphs, source images/documents, homepage books, and structured representations use saved responses in replay mode and their source parsers in live mode. [The source guide](source_journey.md) explains the settings. A missing replay response cannot trigger a live request or sample fallback.

The conversion capture commands and standalone validator have been retired. Existing external recordings can still be read. They must contain the exact requests needed by the selected page. Public page JSON is not a substitute for an unchanged upstream response.

Run the reader's tests with `uv run ./run_tests.py vivo_app.tests.test_recorded_responses -v`. They create invented responses in a temporary directory outside the repository. No authentic record or publication content is included.
