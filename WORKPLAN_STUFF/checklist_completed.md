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

No whole URL cases are certified by batch-001. Fifteen individual improvements have deployed evidence, recorded below. Do not equate these results with completion of S07 or owner acceptance.

For each completed case, record the original pending ID, stable case ID, safe URL pattern and variation, required checks, deployed revision, comparison date, evidence label, result, and owner acceptance if required. Keep exact URL bindings and identifying observations private. Leave other variations pending. If a regression appears, return the affected case to `checklist_todos.md` and record when and why it was reopened.

Every required URL-pattern endpoint must have visual confirmation against Rails before being added as complete. Include the visual result and inspected page or artifact in its completion record, alongside functional and response checks.

## Individual improvements verified after deployment

- [x] **2026-10-03 — batch-001 citation and link improvements 01, 05, 11–14, 18–20, and 22.** Applicable source variations matched Rails citation text or inline formatting; padded DOI, PubMed, and website links reached the intended articles. Revision `e0cec5a`; cases P08–P15; private evidence label `batch-001-profile-checks`. See the [evaluation report](previous_workplan_artificts/batch_001_evaluation.md) for each result and limitations.
- [x] **2026-10-03 — batch-001 navigation and section improvements 25–29.** Checked direct-entry search return, actual filtered/paged search return, institution descriptions and search destinations, and active section state through controls, bookmarks, and keyboard use. Revision `e0cec5a`; cases P01 and P08–P12; private evidence label `batch-001-profile-checks`. Whole URL comparisons and owner acceptance remain pending.
