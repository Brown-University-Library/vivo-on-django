# Workplan v2: complete the public Rails-to-Django replacement

Proposed by Codex and reviewed by the owner on September 27, 2026. Updated that day to use the development server first, adopt `httpx2`, and explain environment settings. The owner's approval of this plan does not mean that its implementation or final site acceptance is complete.

**Recommendation:** extend the existing Playwright comparison command, use `httpx2` alongside it for response capture and checks, and make an early, restricted development-server installation the next milestone. Start that installation with prepared data. Then connect one search-to-profile journey to real sources before expanding across the remaining endpoint families. Continue local appearance work throughout. The separate production installation follows when available.

Keep [PLAN__workplan.md](PLAN__workplan.md) unchanged as the v1 history. Use this v2 for the proposed next steps; use [GOAL.md](GOAL.md) and the [public endpoint scope](docs/public_endpoint_scope.md) for scope, and [AGENTS.md](AGENTS.md) for coding practices. The goal remains that regular visitors notice no difference in URLs, content, behavior, or appearance, except differences explicitly accepted by the owner.

Contents:

- [Where the work stands](#where-the-work-stands)
- [Comparison tooling and expected savings](#comparison-tooling-and-expected-savings)
- [Early server installation and environment settings](#early-server-installation-and-environment-settings)
- [Stages and completion milestones](#stages-and-completion-milestones)
- [Capture, fix, and compare cycle](#capture-fix-and-compare-cycle)
- [Final completion requirements](#final-completion-requirements)
- [Immediate next tasks](#immediate-next-tasks)

## Where the work stands

The owner's original three stages remain useful: determine the required URLs, gather evidence and data, and implement matching pages and behavior. Evidence gathering and implementation can overlap. V2 adds explicit server milestones and a final acceptance stage, without restarting completed discovery.

| Area | Established so far | Still needed |
| --- | --- | --- |
| Stage 1: required URLs | Complete. The approved scope includes public pages, supporting formats, assets, and compatibility redirects. The external discovery manifest contains 62 case specifications. | Extend scope only if concrete evidence shows a currently used requirement or a dependency of an included journey. Specifications are not passing comparisons. |
| Stage 2: public response evidence | Many real Rails responses, browser observations, downloads, and assets have been saved. They already support selected local journeys. | Fill specific endpoint and content-variation gaps; align new captures with the data used for comparison. Do not repeat settled discovery merely to reorganize the plan. |
| Stage 2: authentic source processing | A reader validates saved upstream responses. Local search, person profiles, ordinary and specialized organizations, search JSON, organization publication TSV, full facets, supported CV PDFs, nested profile JSON, and basic graph pages and downloads use bounded source processing. | Verify more nested records, connect live visualization access, match graph interactions and previews, and add other source services. This remains the main unfinished part of stage 2. |
| Stage 3: behavior and appearance | Selected search, profile, organization, homepage, and redirect work is implemented. A reusable browser comparison command exists. | Complete all included families and interactions, expand automated coverage, and resolve visual differences. |
| Server verification and acceptance | Local setup and offline journeys have recorded checks. | Verify restricted server installations, real service access, broader matched queries, and the owner's final walkthrough. |

The latest [external checkpoint](../stage2_work/organization_home/README.md) records bundle `2026.09.27.3`, with 70 exact requests and 190 assets. It reports 72 passing repository tests and selected offline browser and response checks. Selected screenshots match closely or exactly. A later focused check found that the homepage's stable layout matches pixel for pixel when its changing background and separately verified cover pixels are hidden. The small organization desktop difference is limited to synthesized bold text drawn from the same font in a different file format. See [the visual findings](docs/conversion/visual_comparison_findings.md). Many links outside the prepared journeys remain unavailable. These counts describe different things; 70 saved requests do not mean all 62 discovery cases are implemented or accepted.

On September 27, 2026, Codex also checked prepared mode with `DEBUG=False`, validated the prepared bundle, and ran `collectstatic` without duplicate-file warnings after correcting static-file discovery. [The server guide](docs/server_setup.md) records the first installation steps. The comparison command now supports named cases, rerunning cases that did not pass, focused screenshot CSS, concise terminal results, and a configured target-server mode. Its controlled browser checks pass. The actual development-server installation and its HTTPS choices still belong to the owner and system administrator.

Those are previously recorded results, not tests rerun for this planning task. The checkout reviewed for v2 is revision `405a2b7` and was clean before this document was added. Older checkpoint statements about uncommitted implementation describe their original milestones.

On September 28, 2026, a local preview check found that debug had been disabled, so ordinary `runserver` returned pages without their application styles, scripts, and branding images. The local configuration now enables debug, and `runserver` explains this condition at startup. A fresh local process showed the prepared homepage, profile, and search layouts correctly; the profile publication filter and initial homepage covers were also checked in the browser. All 84 tests, changed-file Ruff checks, Pyright with the project interpreter and basic checking, and bundle validation passed. See the [local preview troubleshooting steps](docs/prepared_data.md#if-local-pages-look-unstyled). This initial correction restored access to the existing prepared presentation. The subsequent font work is recorded under Stage 3 below. Prepared coverage and live source processing remain unchanged.

On September 28, 2026, Codex used local source access to connect one selected search-to-person-profile journey. The new client requests Solr search results, an exact person record, and an affiliation record, then serves the corresponding images. A bounded command saved six original responses outside Git. The same processing rendered the unfiltered search, the People-filtered search, and the person profile in live and offline replay modes; an uncaptured replay request returned 503 without contacting a service. That was the first source-backed HTML scope. Other page families, formats, and source services remained unfinished. [The source journey guide](docs/source_journey.md) gives current configuration and limits.

A matched local browser comparison found the selected search and profile visually close to the public pages: changed pixels were about 0.4% and 1.2% of the captured desktop viewports. The People-filtered search showed the same selected text and about 0.4% changed pixels. After selecting View All, visible text in all five profile sections matched the public page. Further checking found that Chrome's GPU rendering gave identical portrait bytes slightly different pixels at the two site addresses. A new reference and local capture with GPU rendering disabled showed zero changed pixels for both desktop pages. The cases still need review because optional public requests failed during capture; those failures remain visible in the reports. The selected pages loaded their core content and images. This local result does not verify access from the development server or acceptance across other people, queries, and widths. Some v1 passages and older supporting documentation still describe now-existing prepared-data or comparison code as future work; the current code and the specific status statements above resolve that historical ambiguity.

Later on September 28, the local source connection resumed. Four more person journeys were captured outside Git and replayed, covering profiles with one to six visible sections and zero to 165 publications. An expanded capture included no-results, later-page, and repeated-filter searches; a linked organization; one batch Solr lookup for its members; full search facets; and a CV PDF. The organization showed all 58 public member rows with matching visible text and loaded images. The selected facet response matched the public values and link query parameters, and the replayed CV matched the public PDF bytes. Its desktop screenshot differs by about 0.3%, localized to a visualization preview that still needs its own source work. These results are local; server access and broader records remain to be checked.

The next local increment added source-backed search JSON, an ordinary organization's publication TSV, a selected active-team page, sparse profile JSON, and visualization graph JSON request paths. The team definition stays outside Git; one Solr request supplied its four members and their portraits. Its member names and titles matched the saved public page, with a different order between capture dates. The organization TSV contained the same 1,355 public data rows by content, also in a different order. One sparse profile JSON comparison matched 34 of 35 public fields; its update date changed between captures. A fixed-member organization now reads its additional member IDs from that external definition file. A later matched local capture showed all 13 displayed members and all 272 publication export rows by content. The research-area organization combines external member IDs with one bounded Solr query; all 74 displayed names matched the saved public page, with one title changed between captures. Nested profile JSON conversion and graph HTML/CSV have made-up local tests. Three varied nested profiles were compared with public JSON and Solr responses. The strongest matched 33 of 35 top-level fields, including every publication, appointment, training entry, and collaborator in order. Another confirmed the credential ordering and all 97 publications shared by its public and Solr responses; the public response had 14 additional publications. Coauthor and collaborator CSV downloads matched saved public downloads byte for byte when built from their saved graph JSON. Live visualization access, custom-member graph calculation, graph interactions, and organization preview remain unfinished. New source checks used a few bounded, paced Solr requests rather than a broad sweep.

`PAGE_DATA_MODE` is one setting that chooses where Django gets page content. `prototype` selects existing sample pages; `prepared` reads saved data already arranged for the pages. `replay` reads exact saved, unprocessed service responses for the supported search, profile, organization, facet, and CV journey and runs Django's processing on them. `live` requests current data for that journey and runs the same processing. Use `prepared` for the first installation because it covers more page families. Extend replay/live by complete journeys without silently substituting prepared or sample data.

Keep these three kinds of evidence distinct:

| Evidence | What it tells us | What it does not tell us |
| --- | --- | --- |
| Rails public responses and browser captures | What a visitor receives, sees, and can do. | The exact requests Rails makes to Solr or another service. |
| Prepared page data | Whether selected templates, assets, and interactions can reproduce saved observations. | Whether Django requests and transforms authentic source data correctly. |
| Raw upstream request/response recordings | Whether Django can process authentic service responses when replayed through its real processing code. | Whether arbitrary new queries work against the live service or whether Rails had the same source state. |

Keep real people’s records, publications, saved responses, and screenshots outside Git. Tests and examples committed to the repository should use made-up names and records instead. This does not prevent local comparisons from using the real data stored beside the checkout. Existing local materials include the [discovery manifest](../public_site_review/planning/public_cases.json), [feature coverage](../public_site_review/planning/public_feature_coverage.md), and checkpoint directories. They are not included in a standalone clone.

## Comparison tooling and expected savings

**Use both Playwright and `httpx2`.** The owner has selected `httpx2`, the Python package continued from HTTPX, for future HTTP clients. It retrieves responses and their metadata. Playwright runs a browser, so it can exercise JavaScript, observe the rendered page, and save screenshots. See the official [HTTPX2 migration documentation](https://pydantic.dev/docs/httpx2/get-started/migration/), [Playwright screenshots documentation](https://playwright.dev/python/docs/screenshots), and [browser network documentation](https://playwright.dev/python/docs/network). Add `httpx2` to application dependencies when implementing source access; it is not yet used by the current application.

| Method | Best use in this project |
| --- | --- |
| `httpx2` | Save raw response bodies; check each redirect hop, status, relevant headers, JSON, RDF, CSV/TSV, PDFs, and images; request upstream data from Django's source clients. It does not lay out CSS or execute page JavaScript. |
| Playwright | Repeat search/filter/profile journeys; check controls, keyboard focus, browser Back, downloads, and JavaScript-dependent content; capture matched desktop and narrow screenshots. Rendered positions and computed styles can help diagnose differences when needed. |
| Interactive browser use | Discover an unfamiliar interaction, inspect an unexpected difference, and review screenshots or behavior that automated assertions do not explain. Convert recurring checks into saved cases. |

Playwright does not independently judge whether two sites feel the same. It records observations and runs checks that we define. Codex and the owner still interpret unexplained differences. Interactive use of the available browser remains valuable; there is no measured basis here for claiming that its browser engine is inherently more or less token-efficient than scripted Chromium.

### Extend what already exists

[tools/compare_sites.py](tools/compare_sites.py) contains the Playwright code. [pyproject.toml](pyproject.toml) lists `playwright` and `pillow` under `[dependency-groups].dev`, separately from application dependencies. The command and [its usage guide](docs/conversion/browser_comparison.md) provide four modes:

- `capture-reference` visits the configured reference pages and writes observations and viewport screenshots to a new external directory.
- `compare-local` visits the configured loopback Django origin, blocks other browser requests, and compares against a saved baseline without updating it.
- `compare-target` visits the configured restricted Django address and compares against a saved baseline without updating it.
- `self-test` starts a small local test website and checks that deliberate changes are detected. It does not contact the public site.

The command writes JSON, Markdown, and HTML reports with comparison images. It checks selected text, final URLs, status, content type, image loading, and browser failures. Its selected detector checks cover content, navigation, missing elements/assets, and layout changes. It prints a short result, can select named cases, and can rerun cases that did not pass in an earlier report. It is already reusable, but it does not yet provide full redirect-chain coverage, comprehensive download/structured-response checks, or complete page coverage below the viewport. Separate external helpers contain some additional response checks that can be brought into reusable code after removing real-case details.

Extend it in this order, alongside the first source-integration journey:

1. **Make results quick to inspect — complete for current browser cases.** The command prints selected/manifest counts, failures, and the report location. It supports named cases and failed-case reruns. Keep raw bodies, large observations, and screenshots on disk; open only the evidence needed to explain a failure.
2. **Unify response and browser coverage.** Reuse one external case inventory with separate HTTP and browser assertions. Preserve methods, repeated query values, relevant Accept headers, every redirect hop, download metadata, and response meaning. Compare bytes where appropriate; compare structured meaning where serialization differences are harmless.
3. **Use the deployed-site comparison mode — command complete, server run pending.** `compare-target` uses configured reference and target origins and the same cases. The owner still needs to provide an approved way to access the restricted target. The report records the configured data mode, and access failures cannot count as a match. The loopback proof exercised target mode and failed-case selection together.
4. **Expand visual and interaction checks as each family is implemented.** Add captures after scrolling, full-page or element screenshots where useful, download actions, and graph interactions. Add focused checks for layout measurements only when they help diagnose an actual problem.

Do not delay the first server installation until this expansion is finished. Retain `compare-local` for isolated local checks and use `compare-target` when the restricted server is available. A small skill that explains how to run and interpret the command can follow if repeated use shows a need; a skill is not required for the script to be useful.

### Likely savings, and what remains unmeasured

The likely saving comes from repeating known work in ordinary Python: run the cases, calculate differences, save artifacts, and return a compact report. The comparison script itself makes no model calls. Running it manually requires no Codex turn; having Codex run it and investigate failures still uses Codex. Building and maintaining the checks also takes work.

This should reduce repeated browsing and large amounts of response text entering the conversation, especially after CSS or shared-template changes. It may save substantial usage across repeated checks, but no percentage or browser-versus-script cost ratio has been measured. OpenAI documents that task complexity, context, reasoning, tool use, and caching affect usage; shorter tool output alone does not establish a particular saving. See [OpenAI's usage guidance](https://learn.chatgpt.com/docs/pricing#what-are-the-usage-limits-for-my-plan).

After the first reusable journey is stable, compare a small fixed set of checks performed interactively and through the script. Record elapsed time, manual interventions, report size, and task usage if available. Include an unchanged run and a deliberately changed local page. Use this to decide how much further automation is worthwhile, without repeatedly querying production just to measure usage.

## Early server installation and environment settings

**Schedule development-server setup now; schedule broad live comparison after the first source-processing journey works.** The owner will prepare the development server first; a separate installation on the production server follows when available. Early installation can reveal server configuration problems before extensive implementation depends on it. It need not wait for stage 2 to finish. When development data is copied from production, record its refresh date: a change since that copy can explain a difference from the public site.

Use two increments:

1. **Install the current prepared-data application on the development server.** Codex prepares configuration guidance and any necessary setup fixes. The owner and system administrator perform the installation. Check startup, static files, sessions, selected pages, one download, writable application directories, and restart behavior. This proves that the application can run there; it does not prove source integration. Repeat these checks at the restricted production location when that installation becomes available; it is not a prerequisite for starting integration work.
2. **Enable one implemented live journey.** Codex adds the required clients, capture support, and processing. The owner supplies real connection settings and deploys that revision. Run a search, apply/remove a filter, open a profile, and return to the results. Save the upstream inputs so Codex can reproduce differences locally. Expand query variations only as the required processing becomes available.

The second increment is an important part of stage 2, not a final deployment exercise. A parallel installation is especially useful when it can reach the same services as Rails. Being on the same server alone does not ensure that both apps use the same index, request defaults, cache state, or source revision. Confirm those conditions before treating differing results as a Django processing error.

The owner/system administrator maintains the access restriction and separate application configuration. Rails continues serving existing public traffic. Use the normal server application process and static-file setup for the server checks. Verify the chosen access method works from the comparison runner; if Codex cannot reach it, the owner can run the same command from an authorized machine and return the artifact bundle. Production access must not be opened just to make a comparison easier.

### Prepare the `.env` together before the first installation

The updated [example.env](example.env) lists the working settings, explains their purpose, and names the corresponding Rails files and keys where they exist. It identifies the source values used by the supported local journey and leaves future service settings commented. Codex and the owner still need to check the intended launch method and choose installation-specific values. Actual values stay in the installation's private environment configuration.

| Setting or concern | Current implementation and next action |
| --- | --- |
| `DJANGO_SECRET_KEY` | Already read. Supply a separate secret for the Django installation. |
| `DJANGO_DEBUG`, `DJANGO_BROWSER_RELOAD` | Already read. Use `False` for both on the production-parallel installation. Verify behavior with debug disabled before declaring server setup complete. |
| `ALLOWED_HOSTS_JSON` | Already required. Set a JSON list for the intended Django entry point. This setting does not restrict which people can access the site. |
| `STATIC_URL`, `STATIC_ROOT` | Already required. Agree on the URL prefix and collection destination with the server configuration, then check actual CSS, JavaScript, font, and image delivery. |
| `PAGE_DATA_MODE`, `PREPARED_FIXTURE_DIR` | Already read. Use `prepared` and the separately transferred compatible bundle for the first installation. Relative bundle paths resolve against the repository root. |
| Database, cache, and logs | Settings currently use sibling `DBs`, `cache_dir`, and `logs` directories; the database is SQLite. These are not currently selectable through database/cache/log environment settings. Confirm writable locations and isolation, and add explicit settings only if the installation needs them. Installing a database driver alone does not change Django's database configuration. |
| Public links and optional presentation settings | Review existing `MANAGER_URL`, `CONTACT_US_URL_TEMPLATE`, `NOTICE_BANNER`, book-cover settings, and analytics configuration for the selected mode. Preserve required external destinations without sending unwanted test analytics. |
| Source connections, capture, and challenge enforcement | `SOLR_URL`, `IMAGES_URL`, optional `DOCUMENTS_URL`, `UPSTREAM_RECORDING_MANIFEST`, and `UPSTREAM_RECORDING_CASE` support the local search, profile, ordinary organization, facet, and CV journey. A separate bounded command captures that journey outside Git. Other source clients and challenge enforcement still need implementation. `CAPTURE_UPSTREAM_RESPONSES` and `TURNSTILE_ENABLED` are proposals from v1, not working switches. |

Confirm how the actual server process loads the private environment and `.env`, including existing process variables. Check whether the launch method requires proxy, HTTPS, session-cookie, or CSRF settings; add and verify only the settings needed for that deployment. Keep server setup instructions in a dedicated document such as a future `docs/server_setup.md`, outside all READMEs. Use variable names and relative paths in documentation, never explicit server addresses or full server filesystem paths.

## Stages and completion milestones

### Stage 1 — Required URLs: retain the completed result

The [scope table](docs/public_endpoint_scope.md) remains the checklist. Do not reopen unused Manager routes or unobserved formats. Preserve links to separate services and the approved redirect-only boundaries. Keep the Research Areas download-link correction deferred under issue #3. The Django application may also provide the standard `/version/` and `/error_check/` support URLs even though the existing Rails application does not; these are accepted additions rather than Rails-compatibility requirements.

**Completion:** already recorded. A later addition needs evidence of current use or of a dependency required by an included journey.

### Stage 2 — Evidence, real inputs, and early server verification

Proceed through these milestones while continuing useful local appearance work:

1. **Development-server setup works with prepared data.** Complete the first installation increment and `.env` preparation described above. The owner/system administrator checks that environment; Codex resolves application-side setup problems. Repeat on the production server when available.
2. **One journey works with authentic inputs.** Codex traces Rails search and profile processing, implements the minimum `httpx2` clients, and records all necessary source responses. Include supporting lookups, such as record-type and graph-availability requests, rather than treating Solr as the only possible source. Connect replay and live responses to the same parsing and page-data functions, supplying the existing templates.
3. **That journey compares successfully on the server.** The owner deploys it. Codex or the owner runs matched Rails/Django cases, identifies source-data differences separately, and returns any unexplained behavior to local reproduction. Include a query or record not already present in the prepared bundle to demonstrate real source processing.
4. **Extend by endpoint family and content variation.** Add organizations and homepage sources, information pages, representations/downloads, visualizations, remaining compatibility behavior, missing-page behavior, and the configured challenge flow. Order individual tasks by their dependencies and the existing scope table. Reuse captured evidence unless it is missing, inconsistent, or too old for the intended check.

Select varied science, social-science, and humanities examples from the existing feature table. Check actual differences: optional sections present or absent, publication groups, long content, default portraits, available or absent graphs, role groups, custom membership, no results, repeated filters, and pagination. A subject label is useful for sampling, but it does not prove that the relevant variations are covered.

**Stage 2 complete when:** every required family has the authentic inputs or verified static/redirect sources it needs; replay and live modes share request construction and processing where applicable; offline cases run without contacting live services; and the corresponding live connections have been verified. Unsupported inputs and missing recordings fail explicitly. Prepared pages alone never satisfy this milestone. A local Solr installation is optional and should be added only if a specific query check requires it.

### Stage 3 — Matching implementation and appearance: continue during stage 2

For each selected journey, Codex implements the missing Python, templates, CSS, and JavaScript; checks behavior and visual placement; and reruns related completed cases after shared changes. Continue using prepared data for repeatable presentation work while its authentic source processing is being built.

Start by preserving the working search/profile journeys. Resolve the known homepage and organization comparison limits, then extend the remaining families as their inputs become available. Match the visitor's experience; identical source formatting, JavaScript minification, or internal implementation is unnecessary.

Font matching is already required by “as exactly as reasonably possible.” Use the same font files, character ranges, weights, styles, and icon glyphs as the reference pages. A small difference in bold text is still unfinished work unless the owner explicitly accepts it. On September 28, the local implementation switched from the prepared TTF to the exact seven Source Sans Pro WOFF2 files used by the reference stylesheet; the existing icon font was verified byte for byte. [Font sources and behavior](docs/fonts.md) are recorded with the application. Verify those files in browser comparisons at the agreed widths, including bold, italic, and accented text, before declaring the font-related screenshot differences resolved. All eight local font assets match their reference bytes, and the browser loads the local text and icon fonts. The follow-up also corrects the desktop organization heading spacing while preserving the narrow layout. All 87 tests, changed-file Ruff and Pyright checks, bundle validation, and static-file collection pass. Selected browser checks support this change; complete visual acceptance remains outstanding.

Keep views small, source processing under `vivo_app/lib/`, conversion-only commands and comparisons under `tools/`, and public route registration in `config/urls.py`. The Django capture command remains a small entry point for its tool. Add focused behavior and failure tests using Django's test framework or `unittest`. Run the applicable application tests and changed-file Ruff and Pylance checks, using Pyright when Pylance is unavailable. Placeholder text, sample fallback data, or a successful status alone cannot establish a working page.

**Stage 3 complete when:** all required journeys, formats, links, and interactions have functional and visual evidence at the agreed widths, with no unexplained differences hidden by the comparison settings. Source integration and final owner acceptance remain separately required.

### Stage 4 — Full comparison, acceptance, and replacement readiness

Run the complete case inventory from a clean setup and compare the required live journeys. Check desktop and narrow layouts, keyboard navigation, focus, Back behavior, downloads, graphs, and noticeable loading delays. Confirm any additional browser coverage with the owner before the final walkthrough.

Give the owner a short coverage report, links to comparison evidence, and any proposed intentional differences. The owner or a regular site user judges whether the result meets the no-noticeable-difference goal. A parallel installation passing its setup checks is not approval to replace the public Rails site; the eventual traffic switch and recovery procedure belong to a separate owner/system-administrator deployment step.

## Capture, fix, and compare cycle

**Django logging cannot reveal Rails' internal execution.** It can show which requests Django sends, which responses it receives, and how its processing turns them into page data. To understand Rails, Codex must also inspect its source and compare the public output. If those leave a concrete uncertainty about the running Rails implementation, ask for a narrowly selected Rails observation or confirmation from its operator. Installing logging in Django alone cannot answer that uncertainty.

Use this cycle to reduce repeated deployments:

1. **Codex identifies the missing evidence.** Select a small set of case IDs and list the public responses, upstream requests, assets, and processing observations needed. Match the deployed Rails code/settings to the source being inspected where necessary.
2. **Codex implements reusable capture once.** Make capture opt-in and limited by selected cases, request count, size, and duration. Save upstream bytes before transformation, with request method, service-relative path, ordered repeated query values, relevant non-secret headers, status, content type, timestamp, and checksums. Extend the existing GET-only recording format only if a required source needs another method.
3. **The owner deploys a useful increment.** First deploy to development, then the restricted parallel installation as appropriate. Configure service access privately. Capture is disabled in ordinary operation; reusing it for another selected case should normally require configuration, not another logging-code deployment.
4. **Codex or the owner runs the selected cases.** Capture Rails public responses and Django results close together, and record the application revision, source configuration version or non-secret label, data mode, and artifact versions. Explicit HTTP requests run sequentially, with at least 0.3 seconds after each response, including redirect hops. Browser assets may load concurrently within the case limits. Stop on access challenges or unavailable required services.
5. **The owner returns recordings when remote access is unavailable.** Keep response bodies and detailed transformation evidence in dedicated files outside Git. Ordinary logs contain a capture ID, service label, status, timing, and outcome, without raw bodies, credentials, cookies, or identifying query values. Use a private transfer, limited retention, and agreed cleanup for captures.
6. **Codex reproduces and fixes locally.** Replay the authentic responses through Django's real processing, compare the resulting page data with independently observed Rails output, then inspect browser differences. Keep prepared data separate; missing replay inputs cannot trigger live requests or sample substitutions.
7. **The owner deploys the checked change.** Repeat only the necessary live checks and relevant regression cases. Keep earlier captures and reports. Record what changed, what passed, what remains unresolved, and the next responsible person.

If capture fails partway through, keep the successfully saved files and label the run incomplete. Do not treat missing evidence as a pass or overwrite the previous usable baseline. Group related observations into one capture session so each suspected field does not require another deploy.

### Keep comparisons trustworthy

Use the same browser build and operating environment for a screenshot pair, with matching viewport, device scale, locale, timezone, fonts, and interaction state. Both sites can be remote while the same local browser renders them. Wait for the content relevant to the case; capture sections that are only loaded or shown after interaction.

For random homepage imagery, select the same observed state for comparison or use a narrowly documented mask while separately checking image availability and selection behavior. Establish any image tolerance from repeated unchanged captures. Never widen it just to make a failing implementation pass, and never mask missing sections or navigation changes.

For live comparisons, identify source updates, cache timing, and unavoidable date differences before changing code or expected results. If aligned data cannot be established, mark exact content comparison as needing review while retaining any valid structural or interaction checks. A live response must not silently replace an older expected result.

Reports should distinguish pass, fail, blocked, and needs-review results, along with prepared/replay/live mode and selected versus total scope. The current command has a simpler pass/needs-review result; expand it as needed. Required resource failures and unexplained third-party failures remain visible. Any exclusion needs an explicit reason and must not hide a required asset or behavior. Retain a nonzero result for incomplete required checks.

## Final completion requirements

- Every endpoint in the settled scope has an implementation and appropriate HTTP or browser checks, including supporting requests and confirmed variations.
- Authentic source processing works in replay and live modes where needed; prepared-mode success is reported separately.
- A compatible checkout and separately supplied data allow repeatable local checks without production access. Missing inputs do not cause hidden network requests or sample fallbacks.
- The restricted installations have verified configuration, asset delivery, sessions, downloads, and required source access. The owner's `.env` setup is documented with implemented setting names.
- Functional and visual comparisons cover the complete agreed scope. Data drift, blocked checks, and unresolved differences are visible in the report.
- Application tests, relevant comparison detector checks, and changed-file lint, formatting, and type checks pass.
- The owner has reviewed the walkthrough and explicitly accepted any intentional differences. No difference is accepted merely because it is small or longstanding in the prototype.

## Immediate next tasks

1. **Owner/system administrator, with Codex follow-up: install prepared mode on the development server.** Use `example.env` and [the server guide](docs/server_setup.md), establish the launch method and access arrangement, and return any application-side failures to Codex. Local checks with debug disabled, prepared data, and collected static files are complete.
2. **Codex: verify remaining structured responses.** Fixed-member and research-area organization membership now have matched saved public comparisons. Nested profile JSON has made-up local tests and three comparisons with public and raw source captures. Check other record variations as needed; separate source differences from conversion differences and keep Solr requests paced.
3. **Owner, then Codex: verify visualization access and complete linked views.** Graph JSON paths, basic HTML pages, and CSV downloads have local tests, but live visualization-service access is not yet available. When the owner can provide a local tunnel, capture exact graph and availability responses outside Git. Then match the interactive graph pages, profile buttons, and missing organization preview to the public pages. Compare the linked browser journeys and keep optional public-resource failures visible.
4. **Owner/system administrator, then Codex: deploy, capture, and reproduce.** Verify the early installation; deploy the first live journey when ready; return selected captures; fix differences locally and repeat the matched comparison.
5. **Codex: continue stage 2 and stage 3 by complete journeys.** Update this plan with brief dated milestones and remaining work. Preserve v1 and earlier evidence as history; keep detailed real-case reports outside Git.

The initial v2 task added this document. The subsequent review updated its wording, `example.env`, and contributor guidance. The September 27 follow-up added server preparation, comparator improvements, and focused visual findings. Private `.env` values, deployed services, source integration, and deferred scope decisions remain unchanged. The remaining tasks above continue from that point.
