# Application sources

## Contents

- [Configure sources](#configure-sources)
- [Public images and CV files](#public-images-and-cv-files)
- [Organization charts](#organization-charts)
- [Homepage books](#homepage-books)
- [Teams and custom organizations](#teams-and-custom-organizations)
- [Public display downloads](#public-display-downloads)
- [Legacy display JSON-LD](#legacy-display-json-ld)
- [VIVO downloads](#vivo-downloads)
- [Subject librarian reports](#subject-librarian-reports)
- [Failures and diagnosis](#failures-and-diagnosis)

## Configure sources

The webapp reads current source data while serving requests. Keep actual addresses and credentials in the private environment file outside Git.

| Setting | Used for |
| --- | --- |
| `SOLR_URL` | Search, record lookup, membership, facets, and calculated charts/graphs; include the core or collection in the address. |
| `IMAGES_URL` | Profile and affiliation images through Django's source-images route. |
| `DOCUMENTS_URL` | Validated CV PDFs and version redirects through source-documents. |
| `VIZ_SERVICE_URL` | Graph availability lists and ordinary coauthor/collaboration responses. |
| `VIVO_BACKEND_URL` | Original JSON-LD, Turtle, and RDF/XML representations. |
| `VIZ_ENABLED` | Organization visualization display switch. |

Sources have different responsibilities. Profile JSON is distinct from VIVO JSON-LD. Team/custom graphs can be calculated from Solr member records; ordinary graphs use the visualization service. Organization TSV and charts read membership/faculty data. Keep current ordering, metadata, and empty-state behavior.

Startup checks verify required configuration without contacting services. Use sources appropriate to the installation; changing source addresses is a separate operational decision.

## Public images and CV files

Image reads accept up to 20,000,000 bytes; document reads remain limited to 10,000,000 bytes. CV links keep their existing `.pdf` path and optional `dt` query. A successful source response must declare `application/pdf` and have bytes beginning with `%PDF-`. A rejected file returns a friendly HTML 404 page asking the visitor to contact the profile owner. A warning identifies the relative CV filename so the source can be corrected; rejected files do not generate administrator error email. Validation failures remain uncached, allowing a corrected PDF to appear on the next request. Valid PDF bytes, HEAD metadata, and byte-range responses retain their existing behavior. Missing source files return 404; connection and service failures remain 503.

`MEDIA_CACHE_TIMEOUT_SECONDS` sets a separate short lifetime for successful images and CV files, defaulting to 60 seconds. Set it to `0` to disable media cache reads, writes, and locks. Negative or invalid values prevent startup. Change the private environment setting and restart Django to apply a new lifetime. The existing Django file cache and `REPORT_CACHE_LOCK_DIR` coordinate workers, with media keys separate from exports and reports. A source address, file path, document version, timeout, or media-code version change selects a new entry.

The lifetime starts after a successful source read, and cache hits do not extend it. Browser responses use `no-store` so they do not add another cache lifetime. A replacement at the same source path can take up to the configured lifetime to appear after the source makes it available; a new image path or CV `dt` value reads independently. Redirects, 404s, and failures are never stored. An expired file is not returned after a failed refresh. Ordinary profile HTML is unaffected.

## Organization charts

Publication and research-area charts read the complete organization member list in groups of twenty. The total list is not limited to five hundred members. Listed `PEOPLE` and `UNCATEGORIZED` members contribute their available chart data; absent optional publication or research-area fields do not prevent other members from appearing. Member records must still contain a valid JSON object. Existing source-response size limits, small requests, and brief pauses between requests remain in place. An exact organization lookup with zero results returns 404; incorrect or duplicate member IDs, other record types, inconsistent result counts, and source failures remain errors. Existing member ordering and missing-member handling are preserved.

`CHART_CACHE_TIMEOUT_SECONDS` controls a separate cache of successful completed charts, defaulting to 60 seconds. Set it to `0` to disable chart cache reads, writes, and locks. Negative or invalid values prevent startup. The existing Django file cache and `REPORT_CACHE_LOCK_DIR` coordinate workers so simultaneous requests generate a given chart once. HTML, JSON, and CSV for the same chart share the result; publication and research-area charts have separate entries.

The fixed lifetime starts when chart generation succeeds, and cache hits do not extend it. Source changes can take up to the configured lifetime to appear after a completed chart is cached. Browser responses use `no-store` to avoid an additional delay. A changed source address, team or custom membership definition, cache setting, calendar year, or chart-code version selects a fresh entry. Failures and missing organizations are not saved, and expired charts are not returned after a failed refresh. Ordinary profile HTML remains uncached by this mechanism.

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

## Public display downloads

CSV/XML downloads under `/display/` read full faculty records from Solr. Organization downloads use the organization's people, remove repeated faculty IDs, and include the existing custom additions. Configured teams use `TEAM_SOURCE_MANIFEST`. Export reads include `fis_updated_s` and `profile_updated_s`; they do not need portraits or graph availability. These downloads do not read `REPORT_DEFINITIONS_PATH` or require the trusted staff attribute.

`REPORT_CACHE_TIMEOUT_SECONDS` controls public display CSV/XML downloads and subject-librarian reports. It defaults to `28800` seconds (eight hours); set it in `.env` and restart Django to change the lifetime. `0` disables cache reads, writes, and generation locks for both. Both completed download formats share one entry whose lifetime begins after successful generation. Downloading a cached file does not extend its lifetime.

Public cache keys and generation locks are separate from protected-report keys and locks. They use the same Django cache and `REPORT_CACHE_LOCK_DIR`. Changing the source setting, timeout, export version, or applicable private membership definitions selects a new public entry. Definitions are checked on each team/custom-organization request; definition changes during generation stop that attempt. Source faculty and membership changes appear after expiry and regeneration. Failed generation is not cached, and an expired file is not returned after a refresh failure. Concurrent requests wait for the same successful generation, subject to the existing 30-second lock wait limit.

## Legacy display JSON-LD

Ordinary `/display/{id}` requests for records such as `UNCATEGORIZED` return VIVO's JSON-LD. Successful GET and HEAD responses use the existing Django cache and `REPORT_CACHE_LOCK_DIR`, with separate `display-jsonld` keys. A hit returns the saved response without contacting Solr or VIVO. Django still handles every request; this does not configure Apache response caching.

The lifetime uses `DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS` and starts after the successful source reads. The default is 60 seconds, and hits do not extend it. Setting it to `0` disables cache reads, writes, and locks. Negative or invalid values prevent startup. Report and CSV/XML download lifetimes are separate. Responses use `no-store` so browser caching does not add another delay. Entries from the earlier cache version are not reused. A change to either source address, the timeout, or the JSON-LD cache version selects a new entry. Source content and record-type changes become visible after expiry and a fresh lookup. GET and HEAD, trailing-slash forms, and application mount prefixes share an entry for the same identifier.

Only HTTP 200 source responses are saved, preserving their bytes. HTML pages, 404s, exceptions, and requests with unsupported query options are not cached here. Explicit profile JSON, raw JSON, CSV/XML downloads, and `/individual/` representation routes retain their own handling. Other request methods bypass this cache. A failed refresh does not return expired JSON-LD; the next request retries the source reads.

Workers on one server use the shared file lock and recheck the cache after acquiring it, so simultaneous requests can reuse the first successful fetch. Lock waits use the existing 30-second limit. Cache storage or lock failures return the existing display error page.

A timed-out VIVO display request is retried once after a quarter-second pause, while the same generation lock remains held. Each attempt keeps the existing ten-second connection and read limits. A successful retry is cached normally. If the retry also times out, the page returns HTTP 503 with a brief message, the search box, and `Retry-After: 60`. Handled display timeouts log a warning and do not send administrator email. Their responses are not cached; the next request can try again. Other errors retain their alerts. A source timeout while looking up a person, organization, or explicit JSON display also returns this temporary-unavailable response, without retrying those source reads.

HTML and explicit JSON display lookups require exactly one matching source record. A successful lookup with zero results and no documents returns the HTML 404 page, including `json` and `json_txt` requests. Incorrect result counts, mismatched IDs, invalid source data, and unsupported record types remain errors. Missing records are not cached, so a newly available record can appear on the next request.

## VIVO downloads

RDF/XML, Turtle, and JSON-LD downloads under `/individual/` preserve the original VIVO response bytes and their existing content types. Successful GET and HEAD requests use the existing Django file cache and `REPORT_CACHE_LOCK_DIR`. Each record and format has its own entry, separate from display pages and reports. Workers recheck the cache after obtaining the shared lock, so simultaneous requests reuse one successful source read.

`VIVO_EXPORT_CACHE_TIMEOUT_SECONDS` defaults to 60 seconds. The lifetime starts after a successful read, and hits do not extend it. Faculty changes can take up to this lifetime to appear in downloads after the source makes them available. Ordinary profile HTML is unaffected. Set the value to `0` to disable download cache reads, writes, and locks. Invalid or negative values prevent startup. A changed source address, lifetime, or download-code version selects a new entry. Responses use `no-store` so browsers do not add another cache delay.

A source timeout retries once after a quarter-second pause, under the same lock. Both attempts retain the existing source size and time limits. Repeated timeouts return HTTP 503 with “Download temporarily unavailable. Please try again in a minute.” and `Retry-After: 60`. These responses use plain text so an error message is not presented as RDF. Handled timeouts log warnings without administrator email; other source errors retain their alerts. Missing files and failed reads are not cached. A failed refresh never serves expired content, and the next request can try again.

Downloads accept GET and HEAD; other methods return 405 without accessing the cache or source. Invalid or mismatched record IDs and unsupported download suffixes return 404. An optional `format` query value must match the URL suffix and occur only once; otherwise the request returns 400. Other query additions are ignored without changing the source request, cached entry, or expiry. These request errors do not send administrator error email. See [public request behavior](public_behavior.md#pages-and-responses) for image, CV, and chart handling.

## Subject librarian reports

`REPORT_DEFINITIONS_PATH` names a private UTF-8 JSON file. Relative paths resolve against the checkout, independent of the process's working directory. Keep the file outside Git. The report handlers read and validate it on every permitted request, retaining the report-array order. They do not query a Rails database or require report models or migrations.

The file contains `schema_version: 1` and a `reports` array. Each row contains exactly `id`, `user_id`, `name`, `description`, `definition`, `created_at`, and `updated_at`. IDs must be unique positive integers. `user_id` is an integer or null; names, descriptions, and timestamps are strings or null. `definition` is a JSON string with `faculty_ids`, `department_names`, or both, each holding a list of nonempty strings. Unrecognized selection fields are rejected. Empty selector lists are allowed and produce the five section headings without faculty rows. `user_id` does not filter report access.

Use made-up names and records in repository examples; real data stays outside Git:

```json
{"schema_version": 1, "reports": [{"id": 1, "user_id": null, "name": "Example report", "description": "Example selection", "definition": "{\"faculty_ids\":[\"invented-a\"],\"department_names\":[\"Example Department\"]}", "created_at": null, "updated_at": null}]}
```

Generation begins with explicit faculty IDs, then reads every department page from Solr, and removes repeated IDs while retaining first occurrence. Missing faculty are skipped; failed reads and incomplete department paging stop the report. Solr provides current faculty details when the report is generated.

`REPORT_CACHE_TIMEOUT_SECONDS` accepts nonnegative integer seconds and defaults to `28800` (eight hours). `"28_800"` is also accepted. This setting also controls public display CSV/XML downloads. `0` disables cache reads, writes, and generation locks for both for fresh comparisons. Legacy display JSON-LD uses its own short lifetime. Invalid or negative values prevent startup with a clear configuration error. Both report formats share one successful cache entry. Its fixed lifetime begins after generation; downloads do not extend it. A definition-file change selects a new cache entry immediately. Changing the source setting, timeout, or export-code version also selects a new entry. Failures are not cached and expired output is not served after a refresh failure. Protected responses use `no-store`; caching occurs only on the server.

The configured file-based cache and `REPORT_CACHE_LOCK_DIR` coordinate workers on one Unix server. The lock directory defaults to `../cache_dir/report_locks`, relative to the checkout. A waiting request rechecks the cache after obtaining its lock. After 30 seconds of waiting it returns the report error page; staff can retry after the generating request finishes. Process exit releases the lock. Do not remove lock files while workers are running. Separate servers require their own cache and locks, or a separately designed shared-cache arrangement.

`REPORTS_SHIB_ATTRIBUTE` defaults to `Shibboleth-isMemberOf`. Django requires a nonempty value in the trusted request environment; the web server decides who is eligible. This feature adds no Django login, user accounts, or sessions. For local work only, set `REPORTS_ALLOW_LOCAL_DEVELOPMENT=true`, `DJANGO_DEBUG=true`, and run `uv run ./manage.py runserver 127.0.0.1:8000`. The exception is enabled by that loopback-bound development command and requires a loopback client. WSGI and ASGI do not enable it. See [server setup](server_setup.md#protected-reports) for deployment checks.

Replace the JSON file atomically after validating it with `load_reports()` from `vivo_app.lib.reports`. Preserve IDs and original definition strings when transferring rows. A replacement affects the next request; environment changes require restarting Django. Keep a previous copy for recovery.

## Failures and diagnosis

Missing source settings and unusable responses retain their existing errors. Optional image and graph failures retain their existing fallbacks. Restart Django after changing environment values.

`uv run ./manage.py check_dev_sources` checks required source configuration without contacting services. Supplying `--source` makes read-only requests to the named source. See [server setup](server_setup.md#source-checks) for arguments and [development checks](development_checks.md) for local tests. Keep detailed returned records and reports outside Git.
