# Application sources

## Contents

- [Configure sources](#configure-sources)
- [Homepage books](#homepage-books)
- [Teams and custom organizations](#teams-and-custom-organizations)
- [Subject librarian reports](#subject-librarian-reports)
- [Failures and diagnosis](#failures-and-diagnosis)

## Configure sources

The webapp reads current source data while serving requests. Keep actual addresses and credentials in the private environment file outside Git.

| Setting | Used for |
| --- | --- |
| `SOLR_URL` | Search, record lookup, membership, facets, and calculated charts/graphs; include the core or collection in the address. |
| `IMAGES_URL` | Profile and affiliation images through Django's source-images route. |
| `DOCUMENTS_URL` | Supported CV PDFs and version redirects through source-documents. |
| `VIZ_SERVICE_URL` | Graph availability lists and ordinary coauthor/collaboration responses. |
| `VIVO_BACKEND_URL` | Original JSON-LD, Turtle, and RDF/XML representations. |
| `VIZ_ENABLED` | Organization visualization display switch. |

Sources have different responsibilities. Profile JSON is distinct from VIVO JSON-LD. Team/custom graphs can be calculated from Solr member records; ordinary graphs use the visualization service. Organization TSV and charts read membership/faculty data. Keep current ordering, metadata, and empty-state behavior.

Startup checks verify required configuration without contacting services. Use sources appropriate to the installation; changing source addresses is a separate operational decision.

## Homepage books

Configure `BOOK_COVER_DB_HOST`, `BOOK_COVER_DB_PORT`, `BOOK_COVER_DB_NAME`, `BOOK_COVER_DB_USER`, `BOOK_COVER_DB_PASSWORD`, and `BOOK_COVER_BASE_PATH`. The last is an image URL prefix.

The account needs SELECT access to the separate book_covers table. PyMySQL is in the staging/prod groups; for local books use `uv sync --locked --group staging`. This database is separate from Django's SQLite session/application database. Active rows are ordered by publication date and grouped into carousel pages.

## Teams and custom organizations

`TEAM_SOURCE_MANIFEST` names a JSON file outside Git. Relative paths resolve against the checkout. It supplies configured names and fixed members; source services supply their current records.

Use made-up values when documenting the format:

```json
{"teams": {"team-example": {"name": "Example Team", "member_ids": ["invented-a", "invented-b"]}}, "organizations": {"org-example": {"extra_member_ids": ["invented-b"]}}}
```

Missing required definitions produce errors. A configured member absent from Solr is skipped as in the original application. Real files stay outside Git.

## Subject librarian reports

`REPORT_DEFINITIONS_PATH` names a private UTF-8 JSON file. Relative paths resolve against the checkout, independent of the process's working directory. Keep the file outside Git. The report handlers read and validate it on every permitted request, retaining the report-array order. They do not query a Rails database or require report models or migrations.

The file contains `schema_version: 1` and a `reports` array. Each row contains exactly `id`, `user_id`, `name`, `description`, `definition`, `created_at`, and `updated_at`. IDs must be unique positive integers. `user_id` is an integer or null; names, descriptions, and timestamps are strings or null. `definition` is a JSON string with `faculty_ids`, `department_names`, or both, each holding a list of nonempty strings. Unrecognized selection fields are rejected. Empty selector lists are allowed and produce the five section headings without faculty rows. `user_id` does not filter report access.

Use made-up names and records in repository examples; real data stays outside Git:

```json
{"schema_version": 1, "reports": [{"id": 1, "user_id": null, "name": "Example report", "description": "Example selection", "definition": "{\"faculty_ids\":[\"invented-a\"],\"department_names\":[\"Example Department\"]}", "created_at": null, "updated_at": null}]}
```

Generation begins with explicit faculty IDs, then reads every department page from Solr, and removes repeated IDs while retaining first occurrence. Missing faculty are skipped; failed reads and incomplete department paging stop the report. Solr provides current faculty details when the report is generated.

`REPORT_CACHE_TIMEOUT_SECONDS` accepts nonnegative integer seconds and defaults to `28800` (eight hours). `"28_800"` is also accepted. `0` disables report-cache reads, writes, and generation locks for fresh comparisons. Invalid or negative values prevent startup with a clear configuration error. Both formats share one successful cache entry. Its fixed lifetime begins after generation; downloads do not extend it. A definition-file change selects a new cache entry immediately. Changing the source setting, timeout, or export-code version also selects a new entry. Failures are not cached and expired output is not served after a refresh failure. Protected responses use `no-store`; caching occurs only on the server.

The configured file-based cache and `REPORT_CACHE_LOCK_DIR` coordinate workers on one Unix server. The lock directory defaults to `../cache_dir/report_locks`, relative to the checkout. A waiting request rechecks the cache after obtaining its lock. After 30 seconds of waiting it returns the report error page; staff can retry after the generating request finishes. Process exit releases the lock. Do not remove lock files while workers are running. Separate servers require their own cache and locks, or a separately designed shared-cache arrangement.

`REPORTS_SHIB_ATTRIBUTE` defaults to `Shibboleth-isMemberOf`. Django requires a nonempty value in the trusted request environment; the web server decides who is eligible. This feature adds no Django login, user accounts, or sessions. For local work only, set `REPORTS_ALLOW_LOCAL_DEVELOPMENT=true`, `DJANGO_DEBUG=true`, and run `uv run ./manage.py runserver 127.0.0.1:8000`. The exception is enabled by that loopback-bound development command and requires a loopback client. WSGI and ASGI do not enable it. See [server setup](server_setup.md#protected-reports) for deployment checks.

Replace the JSON file atomically after validating it with `load_reports()` from `vivo_app.lib.reports`. Preserve IDs and original definition strings when transferring rows. A replacement affects the next request; environment changes require restarting Django. Keep a previous copy for recovery.

## Failures and diagnosis

Missing source settings and unusable responses retain their existing errors. Optional image and graph failures retain their existing fallbacks. Restart Django after changing environment values.

`uv run ./manage.py check_dev_sources` checks required source configuration without contacting services. Supplying `--source` makes read-only requests to the named source. See [server setup](server_setup.md#source-checks) for arguments and [development checks](development_checks.md) for local tests. Keep detailed returned records and reports outside Git.
