# Public endpoints to reproduce

Updated September 26, 2026. This document records the public behavior selected for the Django replacement, including the owner's review of the previously uncertain examples. It supplements [GOAL.md](../GOAL.md) and [PLAN__workplan.md](../PLAN__workplan.md). Approval establishes scope; it does not establish that a response has been captured, a case has been written, or Django implements it.

All record identifiers, filenames, query values, and service addresses use placeholders or configuration names. Actual examples, owner prompt records, response bodies, and detailed evidence stay outside Git. The decisions apply to endpoint behavior across applicable records, not only the example used during review.

Contents:

- [How to read the data sources](#how-to-read-the-data-sources)
- [Required endpoints and data sources](#required-endpoints-and-data-sources)
- [Preserved links and excluded behavior](#preserved-links-and-excluded-behavior)
- [Not included in the current scope](#not-included-in-the-current-scope)
- [Turnstile configuration requirement](#turnstile-configuration-requirement)
- [Source trace and remaining work](#source-trace-and-remaining-work)

## How to read the data sources

The source column describes the current Rails code, not verified server-to-server recordings. A page can use several sources. Shared templates, styles, images, and scripts also support the rendered pages.

- **Solr:** search and record documents through `SOLR_URL`, including nested `json_txt` content and related faculty lookups.
- **VIVO/Vitro API:** original record representations through `VitroAPI` and `VIVO_BACKEND_URL`. JSON-LD and Turtle exports use this API; Rails does not construct them from its Solr documents.
- **Visualization service:** graph data and cached graph-availability lists through `VIZ_SERVICE_URL`. Its own upstream sources have not been traced.
- **Database:** homepage book rows from `book_covers`. Other database-backed features in the old code do not automatically enter scope.
- **Templates, parameters, files, and external services:** some endpoints render fixed content or redirect using request values. Documents and images come from existing asset locations. The browser challenge uses Cloudflare Turnstile.

## Required endpoints and data sources

This is the complete endpoint list for the current implementation scope, including the nine later approvals. No stage-1 endpoint decisions remain pending. Questions about recording data, serving assets, or testing failure behavior are implementation work, not questions about whether the listed endpoints are included.

Paths are relative to the configured public site. The same `{record_id}` is repeated intentionally in the original VIVO export paths. Query syntax below names supported inputs without prescribing the order of unrelated parameters.

| Method and endpoint | Required behavior | Underlying sources in Rails | Evidence or remaining check |
| --- | --- | --- | --- |
| GET `/` | Homepage, search entry, book carousel, author links, navigation, and changing background image. | Database `book_covers` for ordered active books; templates group them by four. `ApplicationHelper#randomized_background_image` selects among local background assets at render time; no Solr lookup is involved in that selection. | Previous/Next wrap, final short group, image loading on entry, and repeated background selections checked. Representative image delivery and carousel keyboard navigation are also checked. Complete assets and visual comparisons belong to later stages. |
| GET `/search` with `q`, repeated `fq`, `fq_0`, and `page` | Results, facets, highlighting, filters, pagination, empty/no-result searches, and browser return behavior. | Solr through `SearchController` and `Search`. | Previously observed; preserve parameter meaning and ordering of results. |
| GET `/search?q={query}&format=json` | JSON search results. | Same Solr search as HTML; Rails serializes the result data. | Body and HTTP metadata saved locally; response is a JSON array. |
| GET `/search?querytext={query}` | Preserve the older query parameter by redirecting to the current search URL. | Request parameter; destination search uses Solr. | Captured HTTP 302 to `/search?q={query}`, then HTTP 200. |
| GET `/search/advanced` and submissions with `search=true`, `name_t`, `title_t`, `department_t` | Form and redirect to a fielded search. Retain the department parameter even though it was absent from the inspected form. | Templates and query construction; redirected `/search` uses Solr. | Name-only, title-only, combined, and department submissions captured as HTTP 302 to fielded search, then HTTP 200. Empty Advanced submission renders the form with HTTP 200 and no redirect. Back preserves entered values. This does not request a new visible field. |
| GET `/search_facets` with search parameters and `f_name` | Supporting JSON for More dialogs. | Solr search with expanded facet limits. | All three dialog JSON bodies and HTTP metadata saved; selected values agree with earlier browser observations. |
| GET `/display/{person_id}` | Profile sections, conditional controls, publication filtering, links, and search return. | Solr record type and faculty document; visualization-service availability lists may also be read; linked assets. | Previously observed across varied records. Preserve whether a visualization button is shown or hidden. |
| GET `/display/{organization_id}` | Organization content, conditional role groups, member links, and portraits. | Solr type/organization/member documents; some custom memberships use an additional Solr research-area query or a code-defined list. Member faculty loading can read graph-availability lists; templates and assets. | Observed both, single, and absent role groups, including faculty-only custom membership. A team variation is also documented locally; one sample does not establish every configured membership. |
| GET `/display/{person_id}.json` | Profile JSON. | Solr type/faculty data; normal faculty loading can also consult graph-availability lists. | Body structure and HTTP metadata saved locally. Distinct from VIVO JSON-LD. |
| GET `/display/{organization_id}/publications.tsv` | Organization publication download. | Solr type, organization membership, and faculty publication content; `PublicationHistory.details` builds rows. Faculty loading can also read graph-availability lists. | Body and download headers saved locally; compatibility details remain in local findings. |
| GET `/display/` | Redirect to search. | Redirect only; destination search uses Solr. | Captured HTTP 302 to `/search`, then HTTP 200. |
| GET `/display/{person_id}/viz/collab` | Person collaboration view, including its existing empty/error behavior and visibility conditions. | Solr type/profile data and visualization-service availability lists; the browser requests graph JSON. | Empty and populated graph journeys checked. Visible profile entry opens a new tab; expansion and label controls work locally. Fit reloads the direct graph. Preserve existing visibility conditions. |
| GET `/display/{person_id}/viz/coauthor` | Person coauthor view. | Solr profile data and visualization-service availability lists; the browser requests graph JSON. SVG/PNG exports are generated in the browser from the displayed graph; PNG uses a canvas and blob download. | Empty/populated views, navigation, expansion, SVG output, selected keyboard controls, and PNG download checked. Detailed observations remain local. Selected pointer details and neighboring-node navigation are checked. Full accessibility checks belong to later controlled comparisons. |
| GET `/display/{organization_id}/viz/collab` | Organization collaboration view, controls, and graph. | Solr type/organization data; browser graph request. | Scope selection, keyboard activation, SVG output, and PNG export checked; retain with the approved collaboration behavior. |
| GET `/display/{record_id}/viz/collab.json` | Supporting collaboration data for retained person/organization views. | Solr type lookup, then visualization service for ordinary records. Custom membership can instead compute a graph from faculty data. | Organization and person empty/populated data saved. Person CSV control also captured; source converts the graph through `EdgeGraph`. |
| GET `/display/{person_id}/viz/coauthor.json` | Supporting coauthor data for the retained view. | Visualization service through `CoauthorGraph`. | Empty/populated responses and HTTP metadata saved. Populated response uses a `data` wrapper; CSV converts that graph through `EdgeGraph`. |
| GET `/display/{record_id}/viz/collab.csv` | CSV download from retained collaboration views. | Same collaboration inputs as JSON; `EdgeGraph` converts the graph and sets link weights for CSV. | Person and organization responses saved. Served as plain text in the selected captures. |
| GET `/display/{person_id}/viz/coauthor.csv` | CSV download from the retained coauthor view. | Visualization-service coauthor data converted by `EdgeGraph`. | Public response and HTTP metadata saved. |
| GET `/display/{team_id}` for a selected active team | Preserve the observed active-team variation of organization display. | `Team.find_by_id` uses code-defined member IDs and Solr profiles; another branch reads a configured local TSV. | A public team page with member links and a default image was observed. Do not infer that all configured teams are required. |
| GET `/individual/{record_id}` with ordinary browser navigation | Redirect to the display page. | ID and request headers; no Solr lookup in the redirect action itself. | Captured with Accept: text/html: HTTP 303 to display, then HTTP 200. Exact JSON and Turtle Accept values were also checked; both are included in this table. |
| GET `/individual/{record_id}/{record_id}.jsonld` | Original VIVO JSON-LD representation. | `IndividualController` → `VitroAPI` → VIVO/Vitro HTTP endpoint configured by `VIVO_BACKEND_URL`. | Owner verified; body and HTTP metadata saved, JSON-LD parsed. HTTP 200 with `application/json; charset=utf-8`, no redirect. |
| GET `/individual/{record_id}/{record_id}.ttl` | Original VIVO Turtle representation. | Same VIVO/Vitro API, requesting Turtle. | Owner verified; body and HTTP metadata saved, Turtle parsed. HTTP 200 with `text/turtle; charset=utf-8`, no redirect. |
| GET `/people`, `/ous` | Redirect to people/organization filtered search. | Fixed redirect construction; destination uses Solr. | Captured HTTP 302 to the corresponding filtered search, then HTTP 200. |
| GET `/about`, `/help`, `/faq`, `/history`, `/roadmap`, `/help/viz`, `/publications`, `/termsOfUse` | Information pages and their links/anchors. | Templates and linked illustrations/assets. | All eight HTML responses and HTTP 200 metadata saved. `/publications` is a help page, distinct from a record export. |
| GET `/brown` | Preserve existing page behavior and appearance. | Template and linked assets. | Reference HTML and HTTP metadata saved locally. |
| GET `/reports/subject-lib` | Preserve the public entry behavior observed by the owner: redirect to `/`. | Authentication check and redirect; no report dataset is needed to reproduce that observed outcome. | Captured unauthenticated HTTP 302 to `/`, then HTTP 200. Authenticated report lists/downloads are not approved by this observation. |
| GET `/challenge`; POST `/challenge` | Render and verify the browser challenge, with configuration to enable or disable enforcement. | Templates/browser Turnstile script; server-side Cloudflare verification; session state. | Direct GET HTML and HTTP metadata saved. Trigger and verification code traced; runtime POST outcomes and enabled/disabled behavior remain for controlled local checks during implementation. |
| GET `/docs/{bucket}/{filename}.pdf` with observed query parameters | Preserve linked document access. | Existing document files/asset service; profile data supplies the link. | Browser viewing observed; saved HTTP 200 PDF and delivery headers without redirect. Asset ownership/packaging and range-request behavior remain open. |
| GET `/profile-images/{path}`, `/book_cover/{path}`, `/assets/{path}` and other actually used asset paths | Preserve assets required by retained pages. | Existing files/asset service; Solr supplies portrait references, database rows supply book references, templates supply static references. | Representative portrait/default/cover bodies and HTTP 200 metadata saved. Local HTML asset references are inventoried; complete delivery/ownership remains for data preparation. These placeholders do not declare every arbitrary asset path required. |
| GET `/display/{missing_record_id}` and other required missing-page behavior | Preserve useful not-found page and recovery links. | Record type lookup for a missing record; templates for unmatched paths. | Display missing-record page and HTTP 404 captured without redirect; recovery links observed. |
| GET `/display/{person_id}/viz/coauthor_treemap` | Reproduce the treemap and its supporting data/download links. | Solr profile context and visualization-service data; browser draws the treemap using ordinary coauthor JSON/CSV. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/display/{organization_id}/viz/publications`, `.json`, `.csv` | Reproduce the chart, range controls, and supporting formats. | Solr organization/member publication data aggregated by `PublicationHistory`; browser controls select the history range. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/display/{organization_id}/viz/research`, `.json` | Reproduce the view and supporting JSON. Preserve the existing visible download link to collaboration JSON for now. Its correction is deferred in [issue #3](https://github.com/birkin/vivo-on-django/issues/3); do not implement it yet. | Solr organization/member research areas assembled by `AlluvialGraph`; the chart consumes research JSON. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/individual/{record_id}/{record_id}.rdf` | Retain the RDF representation alongside the approved JSON-LD and Turtle formats. | HTTP 200 RDF/XML through the VIVO/Vitro proxy. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/individual/{record_id}` with exact Accept `application/json` or `text/turtle` | Preserve both format-selection redirects. Other Accept combinations remain unverified. | HTTP 303 to the corresponding approved representation; destination uses VIVO/Vitro. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/file/{file_id}/{filename}` | Preserve the old image redirect and working destination. | HTTP 301 to the current image; `ModelUtils.thumbnail_url` constructs its location using `IMAGES_URL`. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/status` | Retain the status response. Caller ownership and controlled failure behavior remain implementation checks, not conditions on this approval. | HTTP 200 JSON in the observed normal state; Rails checks Solr for records. | Approved by the owner; public response evidence is saved outside Git. |
| GET `/services/data/v1/faculty/{person_id}` | Preserve this trailing-slash redirect and existing destination. This approval does not require rebuilding the service or its JSON backend. Confirm routing ownership before configuration changes. | HTTP 301 to the same URL with a trailing slash; no matching Rails route was found. | Approved by the owner; public response evidence is saved outside Git. |

The table covers required endpoint families, not every possible query combination. CSV responses and coauthor SVG/PNG output were inspected on populated person views. Selected keyboard controls were exercised; other interactions and broader accessibility checks remain. Other graph types and historical formats are outside the current list unless new evidence establishes that an included journey needs them.

## Preserved links and excluded behavior

- Preserve the public `/manager` link and its configured destination. Do not rebuild the separate Manager application.
- Do not replicate `/edit/{person_id}` or the unfinished editing workflows. The owner explicitly excluded the reviewed edit entry; reproducing its error is not a requirement.
- Keep the VIVO back end and data-management systems as existing dependencies, rather than rebuilding them.
- Preserve other confirmed external links. Their destinations' workflows and crawler/scanner requests do not become replacement features.

## Not included in the current scope

The following old-code variants are not in the implementation list. Stage-1 evidence did not establish that they are needed by the retained public journeys. They are not a pending review queue and do not require further decisions now.

- Other display exports: CSV, XML, and `json_txt`; organization JSON; and display pages for record types beyond the retained people, organization, and active-team views.
- Home `alias`, `/side_stuff/brown_classic/{name}`, and the generic `/display/{record_id}/viz` entry redirect.
- Search-result sorting and diagnostic parameters, and unobserved visualization variants. Existing facet-dialog sorting remains included.
- Authenticated report lists/downloads and service internals beyond the specifically retained public redirects and links.

This is a current scope boundary, not a claim that those routes never receive traffic. Revisit an item only if development reveals concrete current use or a dependency of an included journey. Record the evidence and update the endpoint list then; the existence of a route in old code is insufficient by itself.

## Turnstile configuration requirement

The current challenge code uses Cloudflare Turnstile. Django reads `TURNSTILE_ENABLED` from the private environment file so the owner can turn search enforcement on and off.

When enabled, search GET requests redirect to the challenge until the visitor completes server-side verification. The pass remains valid for up to 24 hours for the same address. When disabled, ordinary requests do not require the challenge or contact Turnstile; direct `/challenge` requests return 404. Prepared and replay modes require enforcement off so their browser checks stay offline. Tests cover both settings without sending real tokens. Live verification with site keys for the Django hostname remains outstanding. Keep actual keys, session values, and service configuration out of repository content.

## Source trace and remaining work

Source references are paths in the separate Rails checkout: `config/routes.rb`; `app/controllers/{search,display,individual,visualization,home,reports,application,bot_detect}_controller.rb`; and `app/models/{search,model_utils,faculty,organization,vitro_api,coauthor_graph,collab_graph,publication_history,book_cover,team}.rb`. Relevant view templates establish which controls and requests a page uses. Deployed behavior must still be checked against this source trace.

Maintain this table during implementation. For each endpoint/format, distinguish the main data source from related lookups, browser requests, caches, templates, files, and session/authentication checks. Mark unknown dependencies explicitly. Keep actual request/response samples in the outer workspace. The local manifest has 62 specifications, including all nine additional cases approved by the owner. These are not passing automated comparisons. Public responses do not substitute for upstream replay fixtures.

**Stage 1 is complete and the current endpoint list is settled.** The earlier decisions and all nine additional approvals remain in effect. The old-code variants listed above are not pending questions. Preserve the Research Areas download link until the separately tracked correction is scheduled. The next implementation-stage step is supplying prepared search and profile data for local template development, as described in the [workplan](../PLAN__workplan.md#repeatable-data-for-local-development). Authentic upstream capture and processing follow without blocking that initial work. Complete asset packaging, matched visual comparisons, controlled failure/challenge tests, and final acceptance remain later-stage work.
