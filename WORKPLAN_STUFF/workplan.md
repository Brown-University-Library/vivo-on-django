# Workplan: finish the public Rails-to-Django replacement

Updated October 3, 2026. This is the core workplan. Follow [GOAL.md](GOAL.md): preserve the public site's required URLs, used behavior, content, and appearance as exactly as reasonably possible. Read [../AGENTS.md](../AGENTS.md) before each batch for coding directives, checks, privacy rules, and commit guidance.

Contents:

- [Files and responsibilities](#files-and-responsibilities)
- [Current position and priorities](#current-position-and-priorities)
- [Batch workflow](#batch-workflow)
- [Choose and record changes](#choose-and-record-changes)
- [Compare and decide completion](#compare-and-decide-completion)
- [Overall completion](#overall-completion)

## Files and responsibilities

| File or directory | Purpose |
| --- | --- |
| [workplan.md](workplan.md) | Start here; describes who does each step and which records to update. |
| [GOAL.md](GOAL.md) | Defines the intended outcome, exclusions, and success criteria. |
| [public_endpoint_scope.md](public_endpoint_scope.md) | Defines the settled public endpoints, variations, data sources, and preserved links. |
| [checklist_todos.md](checklist_todos.md) | Holds pending URL comparisons, differences, remaining integration checks, and final acceptance tasks. |
| [checklist_completed.md](checklist_completed.md) | Records completed work and its evidence; separates historical local milestones from URLs verified after deployment. |
| [current_batch.md](current_batch.md) | Records the current URLs by safe route pattern, up to thirty specific changes, local checks, commits, push status, and post-deployment results. |
| `../../current_urls.local.md` | Records the exact Rails and Django URLs being evaluated, keyed to the same case and change IDs. It lives in the outer/stuff directory, outside the project repository. From the repository root its path is `../current_urls.local.md`. If absent in another workspace, create it there before selecting a batch. |
| [previous_workplan_artificts/](previous_workplan_artificts/) | Preserves [v1](previous_workplan_artificts/PLAN__workplan.md) and [v2](previous_workplan_artificts/PLAN__workplan_v2.md), including the local v2 edits present during this reorganization. These are historical references. |

The directory name `previous_workplan_artificts` follows the requested spelling. Guides for running comparisons and processing sources remain in [../docs/](../docs/docs_README.md). Server installation instructions remain in [../docs/server_setup.md](../docs/server_setup.md), outside READMEs.

Keep real identifiers, exact URLs, private addresses, record contents, screenshots, responses, and detailed evidence out of tracked files. Keep only safe patterns, non-identifying IDs, aggregate results, and general checks here. Save sensitive evidence in the outer workspace and refer to it by a non-identifying evidence label. The private URL file is outside the repository and is not part of a clone or push. Keep it in the outer/stuff directory. Keep credentials and tokens in private configuration rather than in that file.

## Current position and priorities

Stage 1 is complete: the approved endpoint scope and the existing external discovery manifest define what to reproduce. The manifest previously recorded 62 specifications; that count does not establish implemented or accepted cases. Selected source-backed pages, exports, graphs, local comparisons, and offline checks already exist. Detailed historical results remain in the archived plans. This reorganization does not rerun or certify those results.

Use the current deployed Django application and Rails as the comparison targets. Begin by reconciling existing evidence with the pending checklist, including any already pushed work awaiting deployment or evaluation. Do not restart settled discovery or require a larger offline collection before fixing a demonstrated difference. Verify older statements against the current code and evidence before relying on them.

**Prefer completing an individual URL over implementing one feature across many URLs.** Address that URL's content, interactions, supporting responses, and appearance together. Change shared code when necessary for that URL, then check affected completed URLs for regressions. Choose another URL when the first is complete or a concrete dependency prevents progress; record the reason when moving on.

The separate Manager, unused editing workflows, and VIVO/data-management systems remain excluded. Preserve required external links. Keep the Research Areas download-link correction deferred under [issue #3](https://github.com/birkin/vivo-on-django/issues/3). The previously accepted Django `/version/` and `/error_check/` support URLs are additions, not Rails matching requirements.

## Batch workflow

1. **Codex prepares the batch.** Read this file, `GOAL.md`, `public_endpoint_scope.md`, `checklist_todos.md`, `current_batch.md`, and `../AGENTS.md`. Resume an outstanding deployment/evaluation before starting another batch. Select one URL where possible. Record exact current URLs in `../../current_urls.local.md` (relative to this file); record safe patterns, case IDs, expected Rails behavior, and post-deployment checks in `current_batch.md` before changing code.
2. **Codex makes up to thirty changes on the local workstation.** Count specific fixes or outcomes, not files or commits. A batch may be smaller when a URL is complete, a dependency blocks further work, or related checks need attention. Record each change and its local result. Run the relevant tests, formatting, lint, and changed-Python type checks required by `../AGENTS.md`.
3. **Codex commits and pushes the checked batch.** The owner's October 3 workflow instruction authorizes commits and pushes for subsequent implementation batches serving `GOAL.md`. Follow `../AGENTS.md`: review the exact outgoing changes for sensitive information, group related files into focused commits, and use present-tense messages beginning with a verb, at most ten words. Include safe tracking updates for that batch. Preserve unrelated manual edits. This authorization does not ask for a commit of the initial workplan reorganization or authorize issue closure or a public-site traffic switch.
4. **Codex reports that the batch is pushed.** Record the branch, commit IDs, push result, change count, selected case IDs, local checks, and remaining limits. Tell the owner that it is ready to deploy. If a commit or push fails, record what succeeded and the remaining action; do not describe local commits as pushed.
5. **The owner runs the deploy script and tells Codex when deployment finishes.** Set the batch to `awaiting deployment` after the push. Keep the current URLs and checks available. Codex resumes deployment-dependent evaluation only after the owner's confirmation; elapsed time or a successful push is not deployment confirmation.
6. **Codex evaluates every current URL and changed behavior.** Confirm the loaded revision, then compare Rails and deployed Django using each planned check. Include relevant completed URLs when shared code changed. Record per-change and per-case outcomes; a revision check alone does not demonstrate matching behavior.
7. **Codex updates the checklists and prepares the next batch.** Move a URL case to `checklist_completed.md` only when its required deployed comparisons pass or the owner explicitly accepts documented differences. Keep blocked, untested, and different cases in `checklist_todos.md`. Use every remaining difference to select the next up-to-thirty changes, preferring to finish the same URL. Preserve a dated safe batch report in `previous_workplan_artificts/` before replacing `current_batch.md`; preserve its exact URL bindings and detailed evidence privately.

## Choose and record changes

Give each batch a stable ID such as `batch-001`, and each change an ID such as `batch-001-01`. Carry an unresolved item forward using its original ID or a clear reference to it. Link changes to stable discovery case IDs in the private URL file and safe case records. The initial `S01`–`S38` checklist entries cover scope-table rows; split them into separately tracked URLs, formats, and variations as cases are reconciled. They are not thirty-eight passing comparisons.

For each change, record the observed difference, expected outcome, planned post-deployment check, local result, commit, deployed revision, comparison date, final result, and next action. For each URL, cover all required behaviors and related requests, not just the visible item most recently fixed. Record query values, repeated parameters, headers, and fragments privately when they matter.

Use these states consistently: `not evaluated`, `difference found`, `checked locally`, `awaiting deployment`, `ready for evaluation`, `blocked`, `needs review`, and `verified after deployment`. Record owner acceptance separately. Local success never advances a URL directly to deployed verification. An individual fix can be verified while other behavior on the same URL remains pending.

## Compare and decide completion

Use Playwright for rendered pages, controls, navigation, keyboard use, downloads, and matched screenshots. Use `httpx2` for redirects, status, headers, and response formats. Extend the existing [comparison command](../tools/compare_sites.py) and [guide](../docs/conversion/browser_comparison.md) when reusable checks are needed. Use interactive browsing to inspect a difference that existing assertions cannot explain.

Compare Rails and Django close in time. Keep screenshot pairs on the same browser build and environment, with matching viewport, scale, fonts, locale, timezone, and interaction state. Check desktop and narrow layouts and content revealed by scrolling or controls. Keep required failed requests visible. Explain random imagery or changing source data separately; do not hide missing content or widen a tolerance merely to pass. If data cannot be aligned, retain valid structural checks and mark exact content as needing review.

Run explicit HTTP requests sequentially, waiting at least 0.3 seconds after each response, including redirect hops. Normal browser assets may load concurrently. Stop and record access challenges or unavailable required services. Save upstream responses only when they help reproduce a particular difference or support a useful offline check. Prepared, replay, and live results remain distinct; missing data must not silently select live access or sample content.

Report each current URL's comparison result, each fix's result, remaining differences, blocked checks, and the next action. Count deployed-verified cases separately from local-only cases. A family is complete only after all of its required variations are covered. Reopen a completed case if a later shared change produces a regression. The owner judges final acceptance and proposed intentional differences.

## Overall completion

The pending checklist includes the full endpoint scope, source and asset checks, repeatable offline checks, comparison coverage, and owner acceptance. Finish each required URL and variation with functional and visual evidence. Verify required real service connections and controlled failures, including homepage data and enabled/disabled challenge behavior. Preserve useful local replay without requiring a recording of every possible record or query.

Before final acceptance, run the agreed complete checks from a clean setup, account for unresolved or intentionally different behavior, and give the owner a coverage report and walkthrough. The owner explicitly accepts intentional differences and the replacement. Follow [the later cleanup review](../docs/future_branch_cleanup.md) only after acceptance and ordinary use provide a reason to retire conversion material.
