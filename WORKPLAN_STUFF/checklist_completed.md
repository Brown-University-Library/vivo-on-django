# Completed work and verified URLs

Initialized October 3, 2026. Follow [workplan.md](workplan.md). This record separates historical milestones from URL cases verified after deployment. The reorganization did not rerun application tests or compare live pages.

Contents:

- [Workplan reorganization](#workplan-reorganization)
- [Previously recorded milestones](#previously-recorded-milestones)
- [URL cases verified after deployment](#url-cases-verified-after-deployment)
- [Individual improvements verified after deployment](#individual-improvements-verified-after-deployment)

## Workplan reorganization

- [x] **2026-10-03 — Move private URL bindings outside the repository.** Moved `current_urls.local.md` into the outer/stuff directory, updated its links and all active workplan references, and removed its `.gitignore` entry. Exact URL records remain outside the project repository.

- [x] **2026-10-03 — Set up the batch records.** Centralized the goal and endpoint scope, archived the two previous workplans with existing local edits preserved, added pending/completed checklists and the current-batch form, and updated links. Planning files are local and uncommitted. Validated 13 Markdown files and 129 relative links and anchors; confirmed all 38 scope rows are retained and tracked, both previous plans preserve their text apart from the archive notice and updated links, and the original private URL file was ignored by Git. `git diff --check` passed. No application Python files changed.

## Previously recorded milestones

These entries summarize historical evidence in [v1](previous_workplan_artificts/PLAN__workplan.md) and [v2](previous_workplan_artificts/PLAN__workplan_v2.md). They establish only the selected work described at those checkpoints. They do not establish that whole URL families passed deployed comparisons or that the owner accepted the site.

- [x] **2026-09-26 — Stage 1 scope settled.** Completed endpoint investigation and data-source mapping; the owner approved the nine additional endpoint selections. The existing discovery manifest recorded 62 specifications. These are specifications, not passing comparisons.
- [x] **2026-09-26 through 2026-09-27 — Selected offline journeys.** Added prepared search, profile, organization, homepage, and redirect journeys, bundle validation, assets, and selected browser/response checks. Full integration and site acceptance remained open.
- [x] **2026-09-27 — Reusable comparison tools.** Recorded case selection, repeat comparisons of cases needing review, concise reports, and a configured target comparison mode. Tool availability did not establish deployed coverage.
- [x] **2026-09-28 — Local appearance and fonts.** Recorded restored local static delivery, matched font files, selected layout corrections, and local checks. Broader visual acceptance remained open.
- [x] **2026-09-28 — Selected authentic source processing.** Recorded live/replay search, profile, organization, formats, assets, networks, charts, and status paths, with varied selected comparisons. Source-data differences and broader server checks remained open.
- [x] **2026-09-28 — Homepage and challenge implementations.** Recorded database/replay homepage processing and enabled/disabled Turnstile behavior in local tests. Live database access and actual challenge keys were not verified by those tests.
- [x] **2026-09-28 — VIVO representations.** Recorded workstation access and byte-preserving replay for selected JSON-LD, Turtle, and RDF/XML responses. This did not verify the deployed environment's access.

## URL cases verified after deployment

Nine whole cases are certified under their fixed checks; endpoint families and owner acceptance remain pending.

- [x] **2026-10-03 — P07 sparse profile, revision `a3bca98`.** Five functional and ten visual checks pass: expected controls/content, configured email/Manager destinations, organization navigation, default-search return, required asset evidence, and all five complete desktop/narrow views. The Terms destination now works; font bytes match the bundled files. Private evidence labels `url-batch-003-review` and `url-batch-004-review`. See the [evaluation](previous_workplan_artificts/url_batch_003_evaluation.md). This completes the selected case, not the entire S07 endpoint family.

- [x] **2026-10-05 — P01 rich profile, S07, revision `11fa230`.** All original eight functional and twelve visual checks pass. The complete CV matches every reference byte and all eleven pages are visually inspected; signed-in range/HEAD/unsatisfied-range behavior passes. Overview and complete section views retain matching behavior and layout. Evidence: `url-batch-006-review`; see the [evaluation](previous_workplan_artificts/url_batch_005_evaluation.md). Other S07 variations and owner acceptance remain pending.
- [x] **2026-10-05 — P04 profile without research, S07, revision `11fa230`.** Five original functional, one separately added institution requirement, and ten visual checks pass. Configuration, external links, keyboard/bookmark behavior and footer navigation complete the case. Evidence: `url-batch-006-review`; see the [evaluation](previous_workplan_artificts/url_batch_005_evaluation.md).
- [x] **2026-10-05 — ABOUT01, HELP01, and FAQ01, S24, revision `11fa230`.** Each passes four defined functional and two complete visual checks: full content, navigation/anchors, external/configured links, supporting assets, and desktop/narrow views. About direct-entry aliases and every FAQ anchor are confirmed. Evidence: `url-batch-006-review`; see the [evaluation](previous_workplan_artificts/url_batch_005_evaluation.md). The other S24 pages retain whole-case checks.

- [x] **2026-10-05 — ADVANCED01, S05 advanced form, revision `dedf2c8`.** Four functional and two complete desktop/narrow visual checks pass: form/content and bare/slash entry, submissions with field restoration, internal/external navigation and assets. Earlier unchanged department-submission evidence is retained. Final settled visual pairs match. See the [evaluation](previous_workplan_artificts/url_batch_006_evaluation.md); private evidence label `url-batch-007-review`. Other required S05 variations remain pending.
- [x] **2026-10-05 — EMPTY01, S02 no-results search, revision `dedf2c8`.** Four functional and two complete visual checks pass: query/no-results controls, removal/resubmission/return, query-preserving Advanced search and shared navigation/assets. Whole populated search cases and supporting JSON remain pending. See the [evaluation](previous_workplan_artificts/url_batch_006_evaluation.md).
- [x] **2026-10-05 — O04, S08 organization without member groups, revision `dedf2c8`.** Four functional and two complete visual checks pass: content/conditional controls, search and return, content/shared destinations, required images/assets and all desktop/narrow content through the footer. This variation exposes no member or visualization control. Other organizations remain pending. See the [evaluation](previous_workplan_artificts/url_batch_006_evaluation.md).

For each completed case, record the original pending ID, stable case ID, safe URL pattern and variation, required checks, deployed revision, comparison date, evidence label, result, and owner acceptance if required. Keep exact URL bindings and identifying observations private. Leave other variations pending. If a regression appears, return the affected case to `checklist_todos.md` and record when and why it was reopened.

Every required URL-pattern endpoint must have visual confirmation against Rails before being added as complete. Include the visual result and inspected page or artifact in its completion record, alongside functional and response checks.

## Individual improvements verified after deployment

- [x] **2026-10-03 — batch-001 citation and link improvements 01, 05, 11–14, 18–20, and 22.** Applicable source variations matched Rails citation text or inline formatting; padded DOI, PubMed, and website links reached the intended articles. Revision `e0cec5a`; cases P08–P15; private evidence label `batch-001-profile-checks`. See the [evaluation report](previous_workplan_artificts/batch_001_evaluation.md) for each result and limitations.
- [x] **2026-10-03 — batch-001 navigation and section improvements 25–29.** Checked direct-entry search return, actual filtered/paged search return, institution descriptions and search destinations, and active section state through controls, bookmarks, and keyboard use. Revision `e0cec5a`; cases P01 and P08–P12; private evidence label `batch-001-profile-checks`. Whole URL comparisons and owner acceptance remain pending.

- [x] **2026-10-03 — batch-002-01 citation text and inline formatting.** All 278 selected citations across P08–P12 match Rails on deployed revision `2ba9b1f`, including the five previously different collection titles. Private evidence label `batch-002-profile-checks`; see the [evaluation](previous_workplan_artificts/batch_002_evaluation.md). Full desktop/narrow Publications appearance and whole URLs remain pending. Empty-panel and fresh-bookmark outcomes are not counted as fully verified.

- [x] **2026-10-03 — url-batch-001-01 through 03 selected date and citation outcomes.** Deployed revision `6088911` matches selected date separators and all 345 citation texts and inline-element sequences. The previous expanded sample had three text and one inline differences. Full visual and variation checks remain separate. See the [evaluation](previous_workplan_artificts/url_batch_001_evaluation.md).
- [x] **2026-10-03 — Sparse-profile bookmark outcomes.** All five fresh P04/P07 empty-section and View All bookmarks match Rails on revision `6088911`. This completes the prior bookmark subchecks; asset auditing and whole URLs remain pending.
- [x] **2026-10-03 — P01 keyboard and four visual checks.** P01-F04, P01-V03, P01-V05, P01-V09, and P01-V11 pass on revision `6088911`. Paired Background and Teaching captures include all relevant content and footer at desktop and narrow widths. Private evidence label `url-batch-002-review`; the remaining P01 checks stay open.

- [x] **2026-10-03 — url-batch-002-01 profile heading spacing.** All fifteen compared Affiliations headings match reference padding/height on revision `98cf271`. Populated/empty paired views at both sizes confirm the correction; P01-V04 and P01-V10 now pass. Whole URL checks remain pending. See the [evaluation](previous_workplan_artificts/url_batch_002_evaluation.md).
- [x] **2026-10-03 — url-batch-002-02 and 04 About/Help rendering and appearance.** Both pages render full content and match reference text, illustrations, headings, and inspected desktop/narrow views on revision `98cf271`. Linked destinations and bare About direct route evidence remain pending and are not counted here.
- [x] **2026-10-03 — Selected publication filter behavior.** Thirty-five selected filter states across ten profiles match reference active controls and ordered visible citations with keyboard selection on revision `98cf271`. Full visual, link, and whole-URL checks remain separate. Private evidence label `url-batch-003-review`.

- [x] **2026-10-03 — url-batch-003-01 through 03 information destinations.** All three specified deployed outcomes pass on `a3bca98`: full pages, bare routes/slash aliases, mounted navigation, restored content and inspected desktop/narrow presentation. Forty supporting-page frame pairs match at the fixed measured threshold. Whole information cases retain their remaining checks. See the [evaluation](previous_workplan_artificts/url_batch_003_evaluation.md).
- [x] **2026-10-03 — P01 internal and external link checks.** P01-F05 and P01-F06 pass on `a3bca98`; seven internal destinations preserve their paths/queries, and external/email/configured Manager destinations match. Functional total: 6/8. CV delivery and complete asset coverage remain pending.

- [x] **2026-10-05 — url-batch-004-01 and 02 profile text links and research-area spacing.** Both deployed outcomes pass on `ee0c95f` at desktop/narrow sizes. Full settled P01 views and footer captures complete all twelve visual checks; supporting assets complete F08, advancing functional checks to 7/8. Tiny measured image differences remain recorded. P07's ten visual checks still pass. No additional whole URL completes. See the [evaluation](previous_workplan_artificts/url_batch_004_evaluation.md); private evidence label `url-batch-005-review`.
- [x] **2026-10-05 — url-batch-005-01 and 02 PDF delivery and Overview URLs.** Both pass on `11fa230`; complete document/download comparison and thirty-six correct-dimension bookmark/keyboard/pointer observations confirm the outcomes. Affected P01/P04 views pass and P07 shows no regression. See the [evaluation](previous_workplan_artificts/url_batch_005_evaluation.md).

- [x] **2026-10-05 — url-batch-006-01, 02, 04 and 05 search/homepage outcomes.** Bare generated search/advanced paths and retained slash aliases, query-preserving Advanced search, the named homepage Search button and bare book-author navigation pass on `dedf2c8`. All 98 target book images load; the final two-book group and keyboard carousel wrap pass. The long-title HTML portion passes, but supporting JSON remains pending and is not counted as a complete outcome. Source count/order and whole search/homepage cases remain pending. See the [evaluation](previous_workplan_artificts/url_batch_006_evaluation.md); private evidence label `url-batch-007-review`.
