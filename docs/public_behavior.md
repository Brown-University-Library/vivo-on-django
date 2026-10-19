# Public application behavior

The owner completed the conversion review in October 2026. Preserve the reviewed application's URLs, query meaning, visible content, navigation, and response formats. `config/urls.py` defines registered routes; `vivo_app/views.py` coordinates responses.

## Pages and responses

Paths below are relative to the application's configured browser prefix. IDs, query values, and filenames are placeholders.

| Endpoint family | Behavior to preserve | Source |
| --- | --- | --- |
| `/` | Search entry, navigation, changing background, book carousel, and author links. | Separate book database and cover images; local backgrounds. |
| `/search`, `/search/advanced`, `/search_facets` | Search text, repeated filters, result order, pagination, highlighting, More dialogs, advanced redirects, and browser history. Preserve older querytext redirects. | Solr. |
| `/search?…&format=json` | Existing JSON values, types, order, and encoding. | Solr. |
| `/display/{id}` | Person sections, publication filters, organization groups, member links, teams, portraits, graph and document links. | Solr, images, graph availability, and membership definitions. |
| `/display/{person_id}.json` | Profile JSON handled by the display view, distinct from VIVO JSON-LD. | Solr and graph availability. |
| `/display/{id}.csv`, `/display/{id}.xml`, and `?format=csv` or `?format=xml` | Public faculty, organization, and configured-team attachments with five tables. Suffix and query forms accept a trailing slash on the path. | Solr faculty and membership, private team/custom additions, and the public export cache. |
| `/display/{organization_id}/publications.tsv` | Publication rows, columns, bytes, and download metadata. | Solr membership and faculty data. |
| `/display/{id}/viz/…` | Graphs, treemaps, publication/research charts, controls, exports, and empty states. | Visualization service or calculations from Solr. |
| `/individual/{id}/{id}.{format}` and registered legacy forms | JSON-LD, Turtle, RDF/XML, applicable redirects, Accept handling, and original bytes. | VIVO/Vitro. |
| `/source-images/…`, `/source-documents/…`, `/docs/…`, `/file/…` | Images, documents, PDFs, supported redirects, and legacy links. | Configured sources. |
| `/display/`, `/people`, `/ous`, `/individual/{id}` | Existing redirects and their reviewed destinations. | Redirects and destination data. |
| Informational pages | About, Help, FAQ, terms, history, roadmap, publications, visualization help, institution pages, aliases, and anchors. | Templates and assets. |
| `/reports/subject-lib` and `/reports/subject-lib/` | Protected report list with names, descriptions, and CSV/XML links. | Private JSON definitions. |
| `/reports/subject-lib/{id}`, `/{id}/`, `/{id}.csv`, `/{id}.xml` | Protected attachments containing five tables; XML is an Excel-readable SpreadsheetML workbook. Suffix forms also accept a trailing slash. | Private JSON selectors, Solr faculty, and the completed-report cache. |
| `/challenge` | Configured Turnstile flow, disabled behavior, and sessions. | Turnstile for a configured challenge. |
| `/status`, `/version/` | Status/error behavior and distinction between checkout and loaded revisions. | Solr for status; local revision data for version. |
| `/services/data/v1/faculty/{id}` | Registered handoff to the separate data service. | Existing service outside this webapp. |

Use exact registered routes for suffixes and slash aliases. Keep export routes before the generic individual redirect. An HTTP 200 alone does not establish correct content or download metadata.

Public display downloads use filenames based on the requested ID. Both CSV and XML retain Rails' `application/xml` media type; XML is Excel-readable SpreadsheetML. A CSV/XML suffix takes precedence over the query format. Without a suffix, the last repeated `format` value selects the export. GET and HEAD are supported; other methods for these downloads return 405. Missing source records return the existing HTML 404; source, generation, or cache failures return the existing display error page with status 500. An empty organization produces five headings without faculty rows. Unsupported formats do not fall back to CSV. Existing HTML, JSON, and raw-JSON handling retains its existing validation.

Organizations export each distinct member's full faculty record, including update dates and the faculty's own title and organization label. Custom additions and configured teams use existing membership definitions. Member reads use Rails' twenty-record batches and preserve source order within each batch. Missing members are skipped; incomplete or failed source responses stop generation. Public downloads require neither staff attributes nor report definitions. Their server cache shares `REPORT_CACHE_TIMEOUT_SECONDS` with protected reports, defaults to eight hours, and stores both completed formats together under separate public keys. See [public export sources](source_journey.md#public-display-downloads).

Report URLs check the trusted server attribute before reading definitions or cached downloads. Shibboleth handles sign-in and staff eligibility. Report IDs retain Rails' leading-integer interpretation. A suffix takes precedence over the `format` query parameter; only `xml` selects XML, and other values use CSV. GET and HEAD are supported. Unknown IDs return an HTML 404; unusable definitions, source failures, and report-generation failures return an HTML 500. These URLs do not provide report JSON.

Reports keep Rails faculty order, course/research-area sorting, publication sorting, five section headings, text truncation, filename cleanup, and attachment media types. CSV uses LF rows with CRLF between sections and distinguishes null from empty text. XML uses string cells and numeric escapes for non-ASCII characters. The eight-hour default cache serves both formats from the same faculty reads; see [report configuration](source_journey.md#subject-librarian-reports) for freshness and local development settings.

Search accepts `q`, `page`, `rows`, `fq`, and names beginning with `fq_`, matching the Rails search parser. Other search parameter names are dropped and logged without their values. The search continues using the accepted parameters; dropped names do not become Solr query options. As in Rails, `rows` cannot change the fixed 20-result page size. Existing query-value limits and the allowed filter fields still apply. The views handle `format=json` and the facet selector `f_name` separately.

Ordinary `/display/{id}` requests select the person or organization HTML page using the Solr record type, rather than the ID prefix. Configured `team-` IDs retain their separate membership handling. Other nonempty record types, including `UNCATEGORIZED`, return the original VIVO JSON-LD bytes with the backend's successful or not-found status and `application/json` content type. Missing Solr records or records without a type return the HTML 404 page. Failed source reads retain the display error page. Explicit JSON, raw-JSON, CSV, and XML requests keep their existing handlers.

Successful legacy display JSON-LD responses are cached for GET and HEAD using `REPORT_CACHE_TIMEOUT_SECONDS` (eight hours by default; `0` disables caching). Cache hits skip both source reads. The fixed lifetime starts after fetching the response, and 404s or failures are not saved. HTML pages remain uncached by this mechanism. See [legacy display JSON-LD](source_journey.md#legacy-display-json-ld) for freshness, source changes, and shared-worker behavior.

Collaboration CSV requests through `/display/{id}/viz/collab.csv` or `/display/{id}/viz/collab?format=csv` return HTTP 200 with an empty body when the source supplies a valid empty graph. Empty downloads have no header row, matching other graph downloads without connections. JSON retains the source representation and HTML explains that no collaboration data is available. Missing or malformed graph fields and source failures retain HTTP 503 responses.

The homepage uses a nonempty `alias` to redirect to a local search with the alias encoded as search text. Other homepage parameters are ignored. Display requests use `format` to select a representation and ignore other query parameters, including tracking parameters. Ignored parameters are not passed to source readers or included in the legacy JSON-LD cache lookup. They do not change the response format or extend the cache lifetime.

Display CSV/XML suffixes retain precedence over the query format; without a suffix, the last `format` value selects those downloads. JSON suffixes accept an absent or matching query format. Profile JSON accepts repeated matching `format=json` values; raw JSON accepts at most one `format=json_txt` value. On ordinary and JSON display requests, empty, unsupported, or conflicting formats return HTTP 400 before source reads or cache lookup. Explicit formats continue using their own handlers, separate from the ordinary display JSON-LD cache. Django's configured query-field limit remains enforced. These changes apply to homepage and display requests; other endpoint query rules remain unchanged.

Display identifiers must contain 1–80 ASCII letters, digits, underscores, or hyphens. Recognized `.json`, `.json_txt`, `.csv`, and `.xml` suffixes are removed before checking the identifier. Invalid identifiers return the existing 404 response before cache or source reads, including GET and HEAD requests. Identifiers are not trimmed or decoded a second time. Valid identifiers retain normal missing-record and source-failure handling.

## Supporting services and boundaries

The webapp reads existing services. It does not rebuild Manager, provision Solr, or implement VIVO. External destinations remain separate workflows.

Account/editing routes commented out in `config/urls.py` remain disabled. Their code, templates, models, and migrations are retained at the owner's request. The installation's Shibboleth restriction is managed separately; future browser checks use the access already arranged.

## Maintenance

The application reads configured services. Tests provide made-up source responses to the same processing and rendering code. Preserve existing source-error behavior and optional-source fallbacks.

Use [development checks](development_checks.md) for changes and [source configuration](source_journey.md) for settings. [Historical scope](../historical_conversion_info/original_scope/public_endpoint_scope.md) explains selection of the conversion endpoints; old case statuses are not a current backlog.
