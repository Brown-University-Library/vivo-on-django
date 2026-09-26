# Workplan: reproduce the public R@B site in Django

Initial draft: September 25, 2026. Maintained by Codex and the project owner. Related work: [issue #1](https://github.com/birkin/vivo-on-django/issues/1).

The guiding measure of success is that a regular Researchers@Brown user notices **no difference** after the replacement. Match behavior, content, and appearance closely. Record any proposed intentional difference, explain why it is needed, and obtain the project owner's acceptance before treating it as resolved.

The initial task created this workplan. The repository's [public endpoint scope and data-source table](docs/public_endpoint_scope.md) records required URL patterns using placeholders, including the owner's September 26 decisions. Detailed stage-1 discovery remains in the local [endpoint inventory](../public_site_review/planning/public_endpoint_inventory.md), [feature coverage](../public_site_review/planning/public_feature_coverage.md), and [case manifest](../public_site_review/planning/public_cases.json). Those local files live in the outer workspace and are not part of a standalone repository checkout. Stage 2 has started with local runtime checks and a [saved-response reader](docs/recorded_responses.md); authentic upstream capture, page integration, and comparison tooling remain incomplete. [GOAL.md](GOAL.md) defines the scope; [AGENTS.md](AGENTS.md) defines repository practices. This document supplies the current sequence of work. Earlier plans and route mappings remain historical references where they conflict with that scope.

Contents:

- [Success and scope](#success-and-scope)
- [Starting evidence](#starting-evidence)
- [Sequence of work](#sequence-of-work)
- [Repeatable data for local development](#repeatable-data-for-local-development)
- [Browser comparison tool](#browser-comparison-tool)
- [How Codex works toward completion](#how-codex-works-toward-completion)
- [Completion checks](#completion-checks)
- [Decisions and things to consider](#decisions-and-things-to-consider)
- [Next steps](#next-steps)
- [Completed](#completed)

## Success and scope

Preserve the public site's existing URLs, query behavior, redirects, page content, navigation, downloads, visualizations, and supporting responses wherever current use is confirmed. Include the small details visitors rely on: result order, counts, filter removal, browser Back behavior, profile tabs, image placement, link destinations, and useful behavior at narrower screen widths.

Automated checks provide evidence toward the no-noticeable-difference goal. They do not replace a final walkthrough by the project owner or a regular R@B user. A passing status code, a working Django page, or a low screenshot-difference score alone does not establish success.

Rebuilding the separate Manager application, unused editing features, the VIVO back end, or data-management systems is outside scope. Preserve public links to those services where used. A local Solr instance, if needed, is a development and verification aid; the application must ultimately use the existing services. No redesign or new user-facing features are planned.

**Repository privacy:** keep actual personal names, usernames, profile identifiers, contact information, biographical or CV content, and actual publication titles, author lists, citations, or abstracts out of new repository content. This applies even when the information is publicly available. Keep real-case manifests, feature observations, identifying bindings, captures, screenshots, recordings, and detailed comparison reports in the outer workspace, outside every Git checkout. Case IDs alone do not make the accompanying facts anonymous or suitable for a commit.

The repository may contain general route patterns, tool code, aggregate progress summaries, and deliberately invented examples that do not copy real personal or publication details. Review the exact diff and any proposed fixtures before committing. Do not move real evidence into the repository merely because an automated test needs it; read it through local configuration instead.

## Starting evidence

The initial review found useful code and historical evidence. Later stage-1 browsing verified selected public journeys, and the owner's September 26 review approved additional endpoint behavior. The scope table distinguishes required behavior from unreviewed variants. The remaining stage-1 investigation is now complete for review. Additional observed candidates have explicit recommendations; final scope acceptance and later-stage testing remain open.

| Material | How to use it |
| --- | --- |
| `../rab_primary_url_paths.md`, `../apache_log_analysis.md` | Start a candidate list from historical paths and query parameters. Log hits and successful redirects alone do not establish a real application feature. These files are available in the enclosing workspace, not a standalone checkout. |
| `../vivo-on-rails/config/routes.rb`, controllers, models, presenters, views, and assets | Trace how candidate pages obtain data and render it. Confirm current use in the running site before converting historical features. |
| [config/urls.py](config/urls.py), [vivo_app/views.py](vivo_app/views.py) | Inspect existing routes and handlers before extending them. Many routes currently return placeholders; compare slash handling and redirect behavior with the reference site. |
| [vivo_app/lib/display.py](vivo_app/lib/display.py), [vivo_app/lib/home.py](vivo_app/lib/home.py) | Replace sample data and ID-prefix assumptions as each confirmed feature receives real response fixtures. Account for randomized homepage imagery. |
| [vivo_app/templates/](vivo_app/templates/), [vivo_app/static/](vivo_app/static/) | Reuse useful existing work, following the template actually selected by each view. There are several template layouts. |
| [vivo_app/tests/](vivo_app/tests/), [run_tests.py](run_tests.py) | Keep useful checks, but revise prototype expectations when verified production behavior differs. A successful placeholder response must fail the new comparison checks. |

Rails search and profile code uses Solr documents, including nested data in `json_txt`, and additional data sources may supply some features. Browser observations show what Rails sends to visitors; they do not expose Rails' requests to Solr. Trace each required data dependency separately.

## Sequence of work

1. [Confirm the public endpoints and user journeys](#1-confirm-the-public-endpoints-and-user-journeys)
2. [Establish repeatable data and a runnable local site](#2-establish-repeatable-data-and-a-runnable-local-site)
3. [Build and prove the comparison tool](#3-build-and-prove-the-comparison-tool)
4. [Implement complete public journeys](#4-implement-complete-public-journeys)
5. [Verify the complete scope and obtain acceptance](#5-verify-the-complete-scope-and-obtain-acceptance)

Codex carries out the investigation, tooling, implementation, and checks below within each authorized task. The project owner supplies missing access or data when needed and reviews scope ambiguities and proposed differences. Each phase produces evidence that the next phase can use.

### 1. Confirm the public endpoints and user journeys

1. Combine the historical URL evidence with Rails routes and links in its templates. Group paths by purpose rather than treating each record ID as a separate endpoint.
2. Browse a limited selection of current public pages. Follow navigation, search forms, filters, tabs, and download links; record the additional requests made by those interactions. Run separate scripted web requests sequentially, waiting at least 0.3 seconds after each response before the next request, including redirects. Normal browser loads may fetch assets concurrently.
3. For each candidate, record its path pattern, method, query parameters, response type, redirect behavior, supporting services, evidence source and date, and separate scope and observation statuses. Owner-approved behavior can still lack captured responses. Identify whether Django serves it, preserves a redirect, or links to a separate service. Build out and maintain the repository's [endpoint-to-data-source table](docs/public_endpoint_scope.md): list each required endpoint/format and the underlying Solr, VIVO/Vitro API, visualization-service, database, file, template, or other sources, including related lookups. Use placeholders for all identifying URL parts and keep real responses outside Git.
4. Resolve important uncertainties using current behavior and code. Ask the owner only where evidence cannot establish the intended scope. Do not expand scope merely because an old route or test exists.
5. After confirming the main endpoints, use a browser to find several real examples for endpoint families whose content changes which sections or interactions appear. Codex selects the examples independently through the public site's search and navigation. For faculty profiles, start with approximately six distinct pages: two from the natural sciences, two from the social sciences, and two from the humanities. Use that spread to find varied content; verify the actual features on each page before deciding the sample is sufficient.
6. Define an initial set of 12–24 representative cases across the site, including these examples. Give each a stable ID, starting path, interaction steps, expected observations, and required data. Several cases may exercise the same endpoint. Expand coverage when a confirmed behavior needs another case; the initial count is a starting point, not a completion limit.

Candidate families include home and informational pages; `/search`, `/search/advanced`, and `/search_facets`; `/display/{id}` and linked publication or visualization responses; `/individual/{id}` and confirmed export forms; and linked documents, profile images, book covers, or legacy redirects. Browser-entry or challenge responses need classification if encountered. These are candidates, not a declaration that all are required.

To find faculty examples, Codex follows this browser workflow once the search endpoint is confirmed:

1. Run a few searches through the public site's search form. Start with Chemistry or Physics for natural sciences, Economics or Sociology for social sciences, and English or History for humanities. Try one term per group first and use the alternatives or observed affiliation filters when needed.
2. Follow actual result links and inspect each candidate's displayed affiliations, research information, sections, and controls. A subject keyword match is a lead, not proof of a faculty member's discipline or of a particular page feature.
3. Select distinct profiles that provide the required subject spread and useful feature differences. Add or replace candidates when results repeat or leave feature gaps. This initial discovery can use the available browser directly; it does not depend on the future comparison tool being built.
4. Record the search term, filters used, inspection date, selected relative profile path, case ID, and reason for selection in the local discovery record outside Git. Link each selected case to the local feature observations. Repository progress summaries may report aggregate coverage; keep record-level facts outside the repository even when represented by case IDs.

For each endpoint family with optional content, build a table linking observed features to case IDs. Record which examples show each section or control, which omit it, the data condition that appears to govern it, and the source and date of the evidence. Distinguish an observed absence from a feature that has not yet been checked. Section names suggested during planning are hypothetical until confirmed on the public site.

Include cases with optional sections present and absent, short and long content, and relevant combinations of features that affect layout or interaction. Inspect Rails conditions to guide the search for missing examples, then verify those examples in the running site. Add pages when the initial sample misses a confirmed feature; apply the same approach to organizations and other pages whose presentation depends on their data.

**Deliverables:** a repository [endpoint scope and data-source table](docs/public_endpoint_scope.md) containing only generic route patterns and source descriptions; a detailed endpoint inventory, feature-to-case table, and machine-readable case manifest in `../public_site_review/planning/`, outside the repository. The manifest uses paths relative to the configured site; identifiers and service addresses remain in separate local configuration. Every required family and observed feature must map to a local case or an explicit remaining task. The owner's approved endpoint selections now have local case specifications and public evidence; remaining coverage gaps stay explicit in the inventory and feature table.

**Ready to proceed when:** the first cases have evidence of current use, cover the main public journeys and their observed content variations, and identify which upstream responses and assets are needed to reproduce them. Record gaps explicitly; checking one page does not establish coverage of its whole endpoint family.

### 2. Establish repeatable data and a runnable local site

Prepare the Python 3.12 environment using the locked dependencies and the existing local setup instructions. Check required settings, local directories, startup, and the current test suite; record failures before changing application behavior. Keep environment values outside tracked files.

Trace the selected cases through Rails' data access and capture the minimum complete set of responses needed to reproduce them. Include related lookups and assets, not just a handful of top-level records. Build the replay approach described below first unless the investigation shows that a small Solr setup is the better first step.

**Ready to proceed when:** Codex can start Django, select the saved case data, and run data checks repeatedly without contacting production. Missing recordings cause a clear failure. Real service access remains a distinct, explicitly selected mode.

**September 26 progress:** the locked environment, system checks, migration check, local homepage startup, and original test suite pass. A saved-response reader now checks external manifests, exact requests, case dependencies, and body checksums, with synthetic tests for repeatability and failures. All 44 tests and changed-file type checks pass. Authentic search/profile recordings and upstream connection settings were not found in the inspected workspace locations. Source-derived requests are prepared outside Git, but no real upstream responses have been collected and the reader is not connected to page handlers. Stage 2 remains incomplete.

### 3. Build and prove the comparison tool

Build the Playwright tool described below. Start with a homepage, a search journey, and a profile to prove the approach; extend it to the initial case set. Capture reference evidence early so the prototype's current differences are visible before broad implementation begins.

Prove that the tool detects a changed heading, a wrong redirect or content type, a missing asset, and a visible layout change. These tool checks use a small local test website or controlled local changes. Also show that repeated comparisons of unchanged pages produce stable results.

**Ready to proceed when:** a single command produces a readable report, machine-readable results, and useful visual evidence; failures identify the case and the differing observation. Missing evidence or blocked reference access must never count as a pass.

### 4. Implement complete public journeys

Use the verified inventory to order work. A likely sequence is the shared layout and homepage, search through profile display, organization browsing, confirmed downloads and visualizations, then remaining informational pages and legacy links. Bring each journey's content, behavior, and appearance into close agreement before expanding widely.

For each journey, Codex:

1. Adds or adjusts routes in `config/urls.py`, preserving observed paths, parameters, formats, and redirects.
2. Keeps function-based request handlers in `vivo_app/views.py`; puts query building, service access, data preparation, and reusable rendering helpers in `vivo_app/lib/`.
3. Uses the same data-access code for recorded and real responses, switching only the source of those responses. Uses `httpx` for application HTTP requests.
4. Builds or refines the selected templates and assets. Uses JavaScript where interaction requires it; otherwise prefers Python, templates, and CSS.
5. Adds focused behavior and failure checks. Makes template failures and sample-data fallbacks visible to tests instead of accepting a successful placeholder page.
6. Runs the relevant browser cases, inspects reported text and image differences, fixes them, and checks already completed journeys for regressions.

The current prototype's JSON structures, record-type guesses, and placeholder responses are not the expected answers. Derive expected behavior independently from the reference site and its data.

### 5. Verify the complete scope and obtain acceptance

Run all local cases from a clean setup, then compare the confirmed journeys with the current public site using aligned data where available. Explain data changes separately from implementation differences. Verify the real read-only data connection before claiming completion; replay alone cannot prove that integration works.

Present the owner with the coverage report, remaining differences, and a short walkthrough covering search, browsing, record tabs, downloads, and any confirmed visualizations. The owner judges whether a regular user would notice a change. Record acceptance and any specifically accepted differences; keep unresolved items in Next steps.

## Repeatable data for local development

**Initial recommendation:** replay saved upstream responses at the Django service-access layer, then add Docker Solr if needed to verify query execution. This recommendation remains provisional until the first data dependencies have been traced.

| Approach | What it establishes | Limits and requirements |
| --- | --- | --- |
| Recorded response replay | Given a known request, Django receives the same saved response that supplied the reference case. This can preserve exact result order, totals, facets, and nested records for that case. | Requires authentic request/response pairs. Does not prove that a new query is correct or that real Solr accepts it. Unexpected requests must fail, not return generic sample data or contact production. |
| Small Docker Solr instance | Django's actual query requests run against an index. Useful for filters, query syntax, sorting, and response parsing across varied inputs. | Requires a compatible Solr version, schema, request-handler settings, text analysis, and sufficiently complete records. A small index can change ranking, totals, and facet counts; real records alone do not make its answers equal to production. |

For replay, record the request method, service-relative path, repeated query parameters, relevant headers or body, and response status, content type, and body. Preserve query meaning when comparing request keys, including multiple `fq` values. Record fixtures before Django transforms the response, so the actual parsing and data-preparation code is exercised. Browser request interception can supply browser assets or browser API responses; it cannot replace server-to-Solr recordings.

Keep a fixture manifest linking each case to its requests, responses, capture date, checksums, and reference browser capture. Obtain recordings through authorized service access or an existing export. If neither is available, document that dependency and continue with synthetic data for tool development, clearly marked as insufficient to prove production content matches. Do not derive the expected answer from Django's own output.

Keep raw captures, personal data, publication content, cookies, service addresses, screenshots, and all real-case recordings outside Git checkouts, not merely untracked within them. Repository tests should use deliberately invented fixtures or separately reviewed material containing no identifying information or actual publication content. Removing names alone is insufficient when citations, links, identifiers, or combinations of facts still identify real records. Retain exact real data locally for faithful comparisons; altered names, text lengths, or images cannot establish visual equivalence to the live page.

The first case set should cover these behaviors where confirmed:

- A normal search, a search with no results, and an empty or browse search.
- Filter application and removal, combined filters, pagination, sorting, advanced search, and any separate facet request used by the page.
- The selected real profiles and other record examples from the feature-to-case table, preserving the data that makes each optional section appear or remain absent. Capture the related records and assets needed for each example.
- Navigation from results to a profile and back, including preserved query state.
- Confirmed downloads, alternate response formats, legacy redirects, missing records, and visualization data.
- Homepage data, images, fonts, and other assets needed to render the selected cases without external requests.

Add separate synthetic failure cases for timeouts and malformed service responses. Match documented failure behavior where appropriate without deliberately causing failures on production.

If Docker Solr is needed, pin a compatible image and configuration after checking the actual service requirements. Provide documented start, readiness, load, verify, and reset commands. Loading the same fixture set twice must produce the same local index; reset must target only the disposable local data. Compare results against recorded requests and clearly state where the smaller index limits equivalence. Apache's [Solr in Docker guide](https://solr.apache.org/guide/solr/latest/deployment-guide/solr-in-docker.html) describes running the image with a supplied configuration; it does not establish compatibility with this application's existing schema.

## Browser comparison tool

Use Playwright's Python library within the existing `uv` workflow, with Django tests and `unittest` for supporting checks. Add development dependencies and the browser-installation instructions when implementing the tool. Playwright supports [standalone Python use](https://playwright.dev/python/docs/library), [browser network observation](https://playwright.dev/python/docs/network), and [screenshots](https://playwright.dev/python/docs/screenshots). Implement explicit report generation and image comparison around those capabilities.

The following interface is a proposal; the script and options do not exist yet. An entry point such as `tools/compare_sites.py` would read the external case manifest and local configuration. Proposed configuration names are `CASE_MANIFEST_PATH`, `REFERENCE_BASE_URL`, `LOCAL_BASE_URL`, `FIXTURE_DIR`, and `ARTIFACT_DIR`; store actual values locally. Real-case input and output locations must be outside Git checkouts. The tool must not copy private inputs into repository fixtures or write identifying comparison output into tracked documentation.

| Proposed mode | What it reads and contacts | What it writes |
| --- | --- | --- |
| `capture-reference` | Runs selected public journeys against the configured reference site and its required public resources, with a request limit and delay. Captures observations without changing application records. | Creates a new dated local baseline, preserving earlier captures. Does not silently replace expected results. |
| `compare-local` | Starts or connects to local Django using the selected fixture set; compares it with a saved reference baseline. Permits local services and recorded assets only. | Writes local reports, screenshots, image differences, and debugging evidence. This is the default development check. |
| `compare-live` | Runs the same selected journeys against both configured sites. Identifies whether each comparison has aligned data or possible data drift. | Writes a separate report and captures. Does not automatically update the saved baseline or accept differences. |

The manifest should include case ID, endpoint family, relative path and query, actions, expected final path, assertions, data-fixture reference, viewport, and any narrowly defined normalization. For each example, identify the features it covers and assert which sections and controls should appear or remain absent, along with their content and interactions. Site origins may differ; internal path, query, and fragment behavior must still match. Compare important external link destinations using local expectations.

For each case, return:

- Initial status and redirect chain, final path, response type, meaningful response headers, and relevant download metadata and content checks.
- Visible headings, text, result IDs and order, totals, selected filters, tab state, link destinations, and structured data where applicable. Compare meaning, not raw HTML byte equality.
- Matched screenshots, a difference image, and side-by-side review output at fixed desktop and narrow viewports.
- Browser console errors, failed required requests, and private trace files for failures where useful.
- A result of pass, fail, blocked, or needs review, with the precise differing assertion and links to local evidence. Include fixture and baseline versions, browser version, case counts, and any accepted differences applied.

Provide JSON for Codex and a short Markdown or HTML report for people. A successful command exit requires all selected required checks to pass under recorded rules. Failures, blocked cases, and unresolved review items return a nonzero result. A full-coverage run also fails if required cases are omitted; a small selected run reports its limited coverage prominently.

### Keep comparisons meaningful

Use the same browser build, operating environment, viewport, device scale, locale, and timezone for a screenshot pair. Wait for the relevant content, fonts, images, and interaction state before capture. Establish tolerances by comparing repeated unchanged captures; record them rather than increasing them merely to get a pass.

For randomized homepage imagery or moving elements, select the same observed state where possible or apply a small, documented mask. Separately check that the expected imagery exists and the interaction works. Do not mask missing content, altered navigation, or whole page sections. Preserve raw captures so normalizations remain reviewable.

A dated reference capture and its upstream fixtures must describe the same data state as closely as possible. When that alignment cannot be established, label exact content comparison as needing review. A newer live result can legitimately differ from an older recording; investigate and record the reason before refreshing either. Never refresh the expected output just because Django differs.

Limit production checks to the selected public journeys. Stop and report access challenges or unavailable dependencies rather than bypassing them. Keep reports and traces in the outer workspace. If a repository summary is needed, write a separate account of behavior and checks that contains no actual personal or publication details.

## How Codex works toward completion

Once the tools exist and implementation is authorized, Codex follows this loop without asking the owner to choose every small code change:

1. Read this plan and select the next incomplete case or journey whose dependencies are available.
2. Run its current comparison and identify the earliest cause: request handling, missing data, data preparation, template content, assets, or interaction behavior.
3. Make a focused change and run the corresponding Django or helper tests. Run `uv run ./run_tests.py` for the application check and Pylance, or Pyright if unavailable, for every changed Python file using the project's interpreter and settings.
4. Repeat the local browser comparison and inspect both structured and visual results. Use live checks when a baseline needs validation, not after every CSS edit.
5. Run the completed cases after shared changes. Record remaining differences with a case ID, evidence, next action, and owner; do not label unexplained differences acceptable.
6. Update Next steps and add a brief dated Completed entry only for work actually performed and checked. State limitations and distinguish a reviewable result from owner acceptance.

Codex can refine implementation and tests within confirmed scope. Missing real data, unclear public behavior, and user-visible departures need owner input when the evidence cannot resolve them. Continue independent cases while such questions are open. Baseline changes must be supported by reference evidence; accepting an intentional difference belongs to the owner.

Keep completed entries brief: date, outcome, checks performed, and any remaining limitation or review. Put detailed case results in the comparison reports. Preserve manual edits, leave changes uncommitted unless a commit is requested, and keep issue #1 open for ongoing review.

## Completion checks

- [ ] Every confirmed public endpoint family and user journey has a case, and uncertain candidates have been resolved or explicitly deferred by the owner.
- [ ] Every confirmed feature that depends on record content has representative cases, including presence and absence where meaningful. The feature-to-case table records evidence and remaining gaps; a single passing profile cannot establish completion for all profiles.
- [ ] The initial 12–24 cases, plus cases needed for remaining confirmed behavior, run repeatably with documented data and baseline versions.
- [ ] A clean local setup can run the application and comparisons without production access when fixtures are selected. Missing fixtures or assets produce failures.
- [ ] Required URLs, redirects, parameters, response formats, search results, filters, tabs, links, downloads, and visualizations match the reference evidence.
- [ ] All required pages have been visually reviewed at the chosen viewports; unexplained visible differences remain failures or open review items.
- [ ] The real service connection and current public-site comparisons have been checked, with data drift identified separately.
- [ ] Application tests and changed-file Python type checks pass. Placeholder success responses cannot satisfy the required cases.
- [ ] Proposed intentional differences have an explanation, affected cases, evidence, and explicit owner acceptance. None are accepted by default.
- [ ] The owner or a regular R@B user completes the walkthrough and finds no noticeable change except any specifically accepted differences.

## Decisions and things to consider

| Item | Initial position and next action |
| --- | --- |
| Definition of success | Confirmed by the owner: match behavior, content, and appearance; a regular R@B user should notice no difference. |
| Replay or Docker Solr | Start by investigating replay of authentic responses. Decide after tracing the first cases; add real local query execution where it provides missing evidence. |
| Obtaining real data | Confirm an authorized source of service responses and related assets. Public browser access alone does not supply server-side Solr recordings. |
| Supported browsers and widths | Start with one fixed Chromium environment at desktop and narrow widths. Confirm the actual browser coverage needed before final acceptance. Consider Firefox and WebKit where relevant. |
| Non-Solr dependencies | Identify them during endpoint tracing; supply local recordings or document the integration check needed. Avoid treating Solr as the entire data source without evidence. |
| September 26 endpoint decisions | Replicate the selected person collaboration/coauthor views, JSON-LD/Turtle representations, profile JSON, organization publication TSV, older display/search redirects, JSON search, department search parameter, and additional information page. Preserve the report-list entry's owner-observed redirect to home. Keep Manager as a link and exclude the edit entry. The [scope table](docs/public_endpoint_scope.md) records exact generic patterns and unreviewed variants. |
| Additional September 26 decisions | Retain linked treemap, publication-history and research-area views with their supporting formats; RDF/XML; JSON/Turtle Accept redirects; the old image redirect; and status. Preserve the public faculty-data service trailing-slash redirect without adding its backend to replacement scope. Track the Research Areas download-link correction in [issue #3](https://github.com/birkin/vivo-on-django/issues/3), but do not implement it yet. |
| Challenge configuration | Replicate Cloudflare Turnstile with a boolean `.env` setting to enable or disable enforcement; proposed name `TURNSTILE_ENABLED`. Verify enabled/disabled behavior during implementation. Configuration values remain local. |
| Endpoint-to-data-source table | Initial source trace is saved in the repository. Complete it for each required format and supporting request, including indirect lookups and unknown sources; approval of an endpoint is not proof that its data has been recorded. |
| Baseline upkeep | Keep captures dated and versioned. Agree on refresh frequency after observing how often reference content changes. |
| Automated checks on GitHub | Consider running sanitized offline cases there once the local checks are reliable. Keep private fixtures and reference-site access out of routine automation. |
| Real records and publication details | Keep them outside Git, including case-level observations expressed through case IDs. Repository tests use invented or separately reviewed non-identifying material. |
| Perceived responsiveness and keyboard use | Include representative loading, keyboard navigation, focus, and Back-button checks in the final walkthrough. Record noticeable regressions without turning the conversion into a redesign. |

No intentional user-visible differences have been accepted in this initial draft.

## Next steps

- [x] **Codex: build the candidate endpoint inventory.** Saved the local draft and verified primary public journeys. Uncertain candidates and scope decisions remain explicit in the [inventory outside Git](../public_site_review/planning/public_endpoint_inventory.md); the draft is not owner acceptance.
- [x] **Codex: find and select varied real examples through public-site searches.** Selected two profiles per subject group, then added a seventh to cover missing detail sections and a placeholder portrait. An eighth profile supplies visible visualization links and populated networks. Six selected organizations provide role-group, custom-membership, and team variations. See [local coverage and remaining gaps](../public_site_review/planning/public_feature_coverage.md).
- [x] **Codex: define the first 12–24 cases.** Defined an initial 24, expanded to 26 for two observed gaps, then added 13 for the approved endpoints. The [local manifest](../public_site_review/planning/public_cases.json) now has 62 case specifications, including populated person networks, Advanced-form variations, and additional organization coverage. It records actions, expectations, evidence keys, and required data; all replay fixtures remain missing.
- [x] **Codex: incorporate the owner's September 26 assessments.** Saved the [repository endpoint scope and data-source table](docs/public_endpoint_scope.md), updated local decisions, and retained separate lists of unreviewed variants and unverified behavior.
- [x] **Codex: capture comparison data for the owner-verified JSON-LD and Turtle endpoints.** Saved both response bodies and HTTP details outside Git, parsed both formats, and added local cases. Also captured the other approved endpoints and supporting person graph data. Detailed findings and format differences remain in the [local capture report](../public_site_review/2026-09-26/approved_endpoint_capture/findings.md).
- [x] **Codex: inspect a populated person graph through a visible profile entry.** Followed a visible profile link into a new tab, checked both populated networks and selected controls, and saved supporting JSON/CSV outside Git. Existing hidden/visible conditions remain unchanged. See the [local network findings](../public_site_review/2026-09-26/person_networks/findings.md).
- [x] **Codex: fill the selected earlier HTTP gaps.** Captured entry redirects, the missing-record response, all three facet bodies, Advanced submissions, and CV delivery. Added browser checks for title-only and empty Advanced forms. The [local HTTP findings](../public_site_review/2026-09-26/http_coverage/findings.md) preserve the evidence and remaining limitations.
- [x] **Codex: sample remaining organization variation and profile controls.** Saved five organization responses and added a case for a newly observed variation. Exercised the remaining tabs on a previously selected profile. Findings and narrower remaining gaps stay in the [local organization report](../public_site_review/2026-09-26/organization_roles/findings.md) and [local profile report](../public_site_review/2026-09-26/profile_optional_tabs/findings.md).
- [x] **Codex: check PNG export and keyboard operation on a retained populated graph.** Saved live keyboard observations, two browser downloads, and supporting responses outside Git. Added one case; findings and limitations are in the [local export report](../public_site_review/2026-09-26/coauthor_export_keyboard/findings.md).
- [x] **Codex: check homepage carousel Previous and wraparound.** Checked both boundary directions and the final short group. Also loaded the homepage repeatedly to inspect background selection. Saved observations and public HTML outside Git; see the [local homepage report](../public_site_review/2026-09-26/homepage_carousel/findings.md).
- [x] **Codex: capture representative image delivery details.** Saved and decoded the portrait, default portrait, and book cover responses. Exact URLs and image evidence remain outside Git.
- [x] **Codex: complete the stage-1 endpoint-to-data-source table.** Traced observed pages, formats, custom membership, browser exports, and supporting requests. Explicitly marked separate-service ownership and static delivery configuration as matters for data preparation and operational confirmation.
- [x] **Codex: finish remaining stage-1 investigation and prepare recommendations.** The [local completion assessment](../public_site_review/planning/stage1_completion.md) records the outcomes against all six stage-1 instructions. There are 62 specifications, including nine additional cases now approved by the owner. Complete assets, controlled tests, and matched comparisons remain later-stage work.
- [x] **Owner: review the nine additional scope recommendations.** Keep all nine, preserving earlier approvals. The public faculty-data service approval covers its trailing-slash redirect only. Preserve the Research Areas download link for now; its correction is deferred in [issue #3](https://github.com/birkin/vivo-on-django/issues/3). Source-only possibilities remain explicitly unconfirmed.
- [ ] **Codex: establish data availability.** Obtain the missing upstream settings or existing recordings, capture the prepared search/profile requests with their required lookups, and demonstrate authentic replay. The [reader and usage instructions](docs/recorded_responses.md) are ready for file validation; page integration remains open. Continue with replay first; a local Solr instance is not yet justified by the available evidence.
- [x] **Codex: prepare and check the local runtime.** Verified the locked environment, settings, migration state, startup, and homepage HTML. The original 33 tests passed before changes; 44 tests pass with the new offline-reader checks.
- [ ] **Codex: build the first browser comparison.** Capture a dated reference, compare the selected local pages, and prove that the report detects meaningful differences.
- [ ] **Project owner: review remaining ambiguities and later implementation evidence.** The September 26 selections are accepted scope decisions; remaining variants and proposed differences still need review. Implementation and overall stage-1 acceptance are not complete.

## Completed

(most-recent first)

- **2026-09-26 — Recorded approval of all nine additional cases.** Updated scope, cases, and reference documents while preserving earlier decisions. Limited the public service requirement to its trailing-slash redirect. Created [issue #3](https://github.com/birkin/vivo-on-django/issues/3) for the Research Areas JSON download link and explicitly deferred its correction. No page behavior or application code changed.

- **2026-09-26 — Started stage-2 preparation.** Verified local startup and the existing tests; added an offline saved-response reader, documentation, and invented-data checks. Validated repeated query parameters, missing requests, response integrity, selected cases, and rejection of synthetic data when recorded inputs are required. All 44 tests and changed-file type checks pass. Authentic service data and page integration remain open; no live upstream access, environment edits, commits, or publishing occurred.

- **2026-09-26 — Finished the remaining stage-1 investigation.** Saved representative image delivery, remaining public page responses, selected graph exports/interactions, keyboard behavior, further organization variations, and compatibility candidates outside Git. The local manifest has 62 specifications, including nine proposed candidates for scope review. Updated source responsibilities and separated discovery from later data preparation, comparisons, controlled tests, and owner acceptance. No application code, configuration, commits, or publication changed.

- **2026-09-26 — Checked homepage boundaries and backgrounds.** Added two local cases for 47 total. Verified carousel wraparound, short-group image loading, and changing backgrounds across normal page loads. Traced background selection to template/helper assets and saved identifying observations outside Git. No application code, configuration, or commits changed.

- **2026-09-26 — Checked graph export and keyboard controls.** Added one local case for 45 total. Saved downloaded images, control behavior, accessibility observations, and paced HTTP captures outside Git. Remaining limitations and any proposed intentional differences remain explicit. No application code, configuration, or commits changed.

- **2026-09-26 — Expanded organization and profile interaction coverage.** Saved the limited organization sample and a selected profile journey outside Git. Added one case for 44 total and strengthened an existing case. Updated the remaining coverage limits and next visualization check. No application code, configuration, or commits changed.
- **2026-09-26 — Filled HTTP gaps and checked Advanced-form variations.** Saved complete chains for entry redirects, the missing-record response, facet JSON, Advanced submissions, and CV delivery outside Git. Title-only search preserves its input on Back; an empty Advanced submission keeps the form without redirect. Added two local cases for 43 total. No application code or configuration changed and no commit was made.
- **2026-09-26 — Checked populated person networks.** Followed a visible profile entry and inspected collaboration/coauthor expansion, label visibility, the fit reload, and SVG embed behavior. Saved supporting public responses outside Git and added two local cases. PNG, hover, keyboard, and other listed coverage gaps remain; no application code or configuration changed and no commit was made.
- **2026-09-26 — Captured approved responses and expanded local cases.** Saved public bodies, selected HTTP headers, redirects, and integrity checks outside Git. Parsed JSON-LD and Turtle, inspected person graph empty states, and added 13 case specifications for a total of 39. Updated the scope table and resume notes. Authentic upstream fixtures, populated person graphs, and other listed coverage gaps remain. No application code changed or commits were made.
- **2026-09-26 — Recorded endpoint decisions and initial data-source mapping.** Added a repository document with placeholder-based required endpoints, the owner's selected behavior, exclusions, and unresolved variants. Traced JSON-LD/Turtle to the VIVO/Vitro API and distinguished Solr, visualization-service, database, and asset/template dependencies. Added the Turnstile `.env` switch requirement and a concrete next response check. Updated local reference documents and prompt records. No application code, environment values, or commits changed in this task.
- **2026-09-26 — Kept real-case working documents outside Git.** Moved the inventory, feature table, and manifest to the outer workspace and updated their links. The workplan now explicitly keeps actual personal and publication information, including case-level observations, out of repository content. Checked the remaining diff, document links, JSON, and case references. No application code changed or commits were made.
- **2026-09-25 — Saved stage-1 discovery drafts.** Codex browsed representative public journeys, selected seven profiles and three organizations, traced required source dependencies, and saved the endpoint inventory, feature coverage, and 26-case manifest. Private evidence and identifying bindings remain outside Git. JSON, evidence references, document links, and repository whitespace were checked. HTTP metadata, some candidate families, intended visualization scope, authentic upstream fixtures, and fixed-width comparisons remain unresolved. No application code changed; the drafts are local and uncommitted.
- **2026-09-25 — Added independent discovery of faculty examples.** Following the [browser-search suggestion](https://github.com/birkin/vivo-on-django/issues/1#issuecomment-5836105341), Codex added subject searches, profile inspection, selection criteria, and a local discovery record to the plan. Checked document links, anchors, and formatting. The public-site searches remain future work; no application code changed.
- **2026-09-25 — Added coverage of variations within an endpoint.** Following the [review comment](https://github.com/birkin/vivo-on-django/issues/1#issuecomment-5835976507), Codex added real-page sampling, a feature-to-case table, and corresponding fixture, browser-assertion, and completion requirements. Checked document links, anchors, and formatting. Selecting pages and verifying their features remain future work; no application code changed.
- **2026-09-25 — Initial workplan drafted.** Codex reviewed the repository guidance, goal, prototype routes and helpers, Rails search and display code, and historical URL summaries. The plan now sets out endpoint discovery, repeatable data, browser comparisons, implementation, and acceptance, using the owner's no-noticeable-difference goal. Production behavior, service access, and application tests have not been verified in this planning task; implementation remains future work.
