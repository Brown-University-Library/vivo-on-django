# Live sources and retained data modes

## Contents

- [Configure live sources](#configure-live-sources)
- [Homepage books](#homepage-books)
- [Teams and custom organizations](#teams-and-custom-organizations)
- [Retained offline modes](#retained-offline-modes)
- [Failures and diagnosis](#failures-and-diagnosis)

## Configure live sources

Set `PAGE_DATA_MODE=live` to read current source data while serving requests. Keep actual addresses and credentials in the private environment file outside Git.

| Setting | Used for |
| --- | --- |
| `SOLR_URL` | Search, record lookup, membership, facets, and calculated charts/graphs; include the core or collection in the address. |
| `IMAGES_URL` | Profile and affiliation images through Django's source-images route. |
| `DOCUMENTS_URL` | Supported CV PDFs and version redirects through source-documents. |
| `VIZ_SERVICE_URL` | Graph availability lists and ordinary coauthor/collaboration responses. |
| `VIVO_BACKEND_URL` | Original JSON-LD, Turtle, and RDF/XML representations. |
| `VIZ_ENABLED` | Organization visualization display switch. |

Sources have different responsibilities. Profile JSON is distinct from VIVO JSON-LD. Team/custom graphs can be calculated from Solr member records; ordinary graphs use the visualization service. Organization TSV and charts read membership/faculty data. Keep current ordering, metadata, and empty-state behavior.

Startup checks verify required configuration without contacting services. Use live sources appropriate to the installation; changing source addresses is a separate operational decision.

## Homepage books

Configure `BOOK_COVER_DB_HOST`, `BOOK_COVER_DB_PORT`, `BOOK_COVER_DB_NAME`, `BOOK_COVER_DB_USER`, `BOOK_COVER_DB_PASSWORD`, and `BOOK_COVER_BASE_PATH`. The last is an image URL prefix.

The account needs SELECT access to the separate book_covers table. PyMySQL is in the staging/prod groups; for local live books use `uv sync --locked --group staging`. This database is separate from Django's SQLite session/application database. Active rows are ordered by publication date and grouped into carousel pages.

## Teams and custom organizations

`TEAM_SOURCE_MANIFEST` names a JSON file outside Git. Relative paths resolve against the checkout. It supplies configured names and fixed members; source services supply their current records.

Use made-up values when documenting the format:

```json
{"teams": {"team-example": {"name": "Example Team", "member_ids": ["invented-a", "invented-b"]}}, "organizations": {"org-example": {"extra_member_ids": ["invented-b"]}}}
```

Missing required definitions produce errors. A configured member absent from Solr is skipped as in the original application. Real files stay outside Git.

## Retained offline modes

Prepared mode reads already-arranged pages/assets from `PREPARED_FIXTURE_DIR`; see [prepared data](prepared_data.md). Replay reads unchanged existing service responses from `UPSTREAM_RECORDING_MANIFEST`, selecting `UPSTREAM_RECORDING_CASE`; see [recorded responses](recorded_responses.md). Replay runs the same source processing used for live pages. Neither mode silently switches to live requests when an input is missing.

Prototype is the retained local sample mode and test baseline. These modes remain because of dependencies described in [the review note](code_retirement_review.md). Source-response capture commands are archived; current instructions use existing externally supplied files.

## Failures and diagnosis

Missing source settings, unusable responses, or missing saved inputs retain their existing errors rather than fall back to sample content. Restart Django after changing environment values or selecting a new prepared bundle; bundles are cached per process.

`uv run ./manage.py check_dev_sources` checks the selected mode without contacting services. Supplying `--source` makes read-only requests to the named live source independently of the selected mode. See [server setup](server_setup.md#source-checks) for arguments and [development checks](development_checks.md) for local tests. Keep detailed returned records and reports outside Git.
