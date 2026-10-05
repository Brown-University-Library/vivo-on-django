# Workplan: finish the public Rails-to-Django replacement

Updated October 5, 2026. This is the core workplan. Follow [GOAL.md](GOAL.md): preserve the public site's required URLs, used behavior, content, and appearance as exactly as reasonably possible. Read [../AGENTS.md](../AGENTS.md) before each batch for coding directives, checks, privacy rules, and commit guidance.

Contents:

- [Files and responsibilities](#files-and-responsibilities)
- [Current position and priorities](#current-position-and-priorities)
- [Batch workflow](#batch-workflow)
- [Choose and record changes](#choose-and-record-changes)
- [Compare and decide completion](#compare-and-decide-completion)
- [Measure progress after each deployment](#measure-progress-after-each-deployment)
- [Overall completion](#overall-completion)

## Files and responsibilities

| File or directory | Purpose |
| --- | --- |
| [workplan.md](workplan.md) | Start here; describes who does each step and which records to update. |
| [GOAL.md](GOAL.md) | Defines the intended outcome, exclusions, and success criteria. |
| [public_endpoint_scope.md](public_endpoint_scope.md) | Defines the settled public endpoints, variations, data sources, and preserved links. |
| [checklist_todos.md](checklist_todos.md) | Holds pending URL comparisons, differences, remaining integration checks, and final acceptance tasks. |
| [checklist_completed.md](checklist_completed.md) | Records completed work and its evidence; separates historical local milestones from URLs verified after deployment. |
| [current_batch.md](current_batch.md) | Records improvements to the selected twenty URLs, local checks, commits, push status, and per-change deployed results. |
| [next_batch.md](next_batch.md) | Holds twenty distinct selected URLs by stable case ID, each result, and its specific remaining work. Completed URLs move to the completed checklist; unresolved URLs stay on the next list. |
| [progress.md](progress.md) | Defines repeatable completion checks, current measured results, and the progress report to produce after each deployment. |
| `../../current_urls.local.md` | Records the exact Rails and Django URLs being evaluated, keyed to the same case and change IDs. It lives in the outer/stuff directory, outside the project repository. From the repository root its path is `../current_urls.local.md`. If absent in another workspace, create it there before selecting a batch. |
| [previous_workplan_artificts/](previous_workplan_artificts/) | Preserves [v1](previous_workplan_artificts/PLAN__workplan.md) and [v2](previous_workplan_artificts/PLAN__workplan_v2.md), including the local v2 edits present during this reorganization. These are historical references. |

The directory name `previous_workplan_artificts` follows the requested spelling. Guides for running comparisons and processing sources remain in [../docs/](../docs/docs_README.md). Server installation instructions remain in [../docs/server_setup.md](../docs/server_setup.md), outside READMEs.

Keep real identifiers, exact URLs, private addresses, record contents, screenshots, responses, and detailed evidence out of tracked files. Keep only safe patterns, non-identifying IDs, aggregate results, and general checks here. Save sensitive evidence in the outer workspace and refer to it by a non-identifying evidence label. The private URL file is outside the repository and is not part of a clone or push. Keep it in the outer/stuff directory. Keep credentials and tokens in private configuration rather than in that file.

## Current position and priorities

The owner deployed `ee0c95f`. The [fourth URL-batch evaluation](previous_workplan_artificts/url_batch_004_evaluation.md) verifies both preceding profile corrections. P07 remains the one completed whole case. P01 passes seven of eight functional and all twelve visual checks; full CV/download/delivery comparison remains pending. P04 has ten passing visual checks and a remaining Overview fragment difference.

[Next batch](next_batch.md) contains twenty carried-forward URLs and no additions. [Current batch](current_batch.md) records PDF range delivery and Overview fragment corrections, with their required deployed checks. Full functional and visual evidence remains required for every endpoint and variation. Source alignment remains unresolved. Fresh profile-footer About navigation does not reproduce the earlier slash observation; independent direct-entry coverage and the earlier before-script condition remain pending.

Prefer completing one URL before spreading work across URLs. Change shared code when needed, then check affected completed URLs. Record a concrete dependency when moving to another case before completion. The separate Manager and unused editing workflows remain excluded; preserve required external links. Keep the Research Areas download correction deferred under [issue #3](https://github.com/birkin/vivo-on-django/issues/3).

## Batch workflow

1. **Codex prepares twenty target URLs.** Read this file, `GOAL.md`, `public_endpoint_scope.md`, both checklists, `next_batch.md`, `current_batch.md`, and `../AGENTS.md`. Record the prior deployment's checks first. Keep unresolved URLs with their specific remaining work, then add pending URLs until the list contains twenty distinct URLs. Do not count fragments as separate URLs. A supporting-format endpoint can be selected separately when it has its own approved checks. Save safe case IDs in `next_batch.md` and exact Rails/Django pairs in `../../current_urls.local.md` outside Git. Tell the owner the filename and previous/new counts, then continue working.
2. **Codex improves each selected URL on the local workstation.** Make as many demonstrated, relevant improvements as reasonably possible; there is no fixed improvement count. Prefer finishing one URL's content, interactions, supporting requests, and appearance before moving to another. Record a concrete dependency if progress on that URL is blocked. Check affected URLs whenever shared code changes. Record individual fixes and their expected deployed results in `current_batch.md`. Run the tests, formatting, lint, and changed-Python type checks required by `../AGENTS.md`.
3. **Codex commits and pushes the checked work.** The owner's current instruction authorizes these implementation and workflow commits and pushes. Follow `../AGENTS.md`: review outgoing changes for sensitive information, group related files into focused commits, and use present-tense messages starting with a verb, at most ten words. Preserve unrelated manual edits. This does not authorize issue closure or a public-site traffic switch.
4. **Codex reports deployment readiness.** Record the branch, application and tracking commits, confirmed push, selected URL counts, implemented outcomes, local checks, and remaining limits. Tell the owner when the code is ready to deploy. If pushing fails, explain which commits remain local and the next action.
5. **The owner deploys and tells Codex when it finishes.** Keep the batch in `awaiting deployment`. A push or elapsed time does not establish deployment. Resume checks against the changed deployment after the owner's confirmation.
6. **Codex checks every recorded change and all twenty URLs.** Verify the loaded revision, compare each planned result with Rails, and check affected previously passing behavior. Record passes, differences, partial checks, blocked checks, missing variations, and checks not run separately, with evidence and next actions. A completed evaluation record does not make an unfinished URL complete.
7. **Codex prepares the next twenty URLs.** Move whole URLs to `checklist_completed.md` only after all required deployed functional and visual checks pass, or the owner accepts documented differences. Keep each unresolved URL in `next_batch.md` with specifics about remaining improvements and checks. Add new pending URLs to reach twenty, or record that fewer than twenty remain in the approved scope. Report previous/new counts. Archive the dated safe batch report in `previous_workplan_artificts/` before replacing `current_batch.md`; preserve exact bindings and detailed evidence privately. Continue with the new list without stopping merely to announce it.

## Choose and record changes

Give each URL batch a stable ID such as `url-batch-001`, each row an ID such as `U01`, and each improvement an ID such as `url-batch-001-01`. Preserve original case IDs when a URL carries forward. Historical improvement-count batches keep their original IDs. Carry an unresolved item forward using its original ID or a clear reference to it. Link changes to stable discovery case IDs in the private URL file and safe case records. The initial `S01`–`S38` checklist entries cover scope-table rows; split them into separately tracked URLs, formats, and variations as cases are reconciled. They are not thirty-eight passing comparisons.

Count distinct URLs as batch membership; count improvements separately as implementation evidence. For each change, record the observed difference, expected outcome, planned post-deployment check, local result, commit, deployed revision, comparison date, final result, and next action. For each URL, cover all required behaviors and related requests, not just the visible item most recently fixed. Record query values, repeated parameters, headers, and fragments privately when they matter.

Use these states consistently: `not evaluated`, `difference found`, `checked locally`, `awaiting deployment`, `ready for evaluation`, `blocked`, `needs review`, and `verified after deployment`. Record owner acceptance separately. Local success never advances a URL directly to deployed verification. An individual fix can be verified while other behavior on the same URL remains pending.

## Compare and decide completion

**Every required URL-pattern endpoint must eventually be confirmed visually against Rails.** This is a completion requirement for each endpoint, not just for one representative page in a family or one implementation batch. Record the endpoint, required variation, page or artifact inspected, comparison state, date, deployed revision, result, and private evidence label. For redirects, data responses, downloads, and assets, visually inspect the relevant destination, displayed response, downloaded document, or consuming page and record how it demonstrates that endpoint. Keep the applicable response and behavior checks as well. A successful status code, matching data, or passing local test does not satisfy visual confirmation by itself.

Use Playwright for rendered pages, controls, navigation, keyboard use, downloads, and matched screenshots. Use `httpx2` for redirects, status, headers, and response formats. Extend the existing [comparison command](../tools/compare_sites.py) and [guide](../docs/conversion/browser_comparison.md) when reusable checks are needed. Use interactive browsing to inspect a difference that existing assertions cannot explain.

Compare Rails and Django close in time. Keep screenshot pairs on the same browser build and environment, with matching viewport, scale, fonts, locale, timezone, and interaction state. Check desktop and narrow layouts and content revealed by scrolling or controls. Keep required failed requests visible. Explain random imagery or changing source data separately; do not hide missing content or widen a tolerance merely to pass. If data cannot be aligned, retain valid structural checks and mark exact content as needing review.

Run explicit HTTP requests sequentially, waiting at least 0.3 seconds after each response, including redirect hops. Normal browser assets may load concurrently. Stop and record access challenges or unavailable required services. Save upstream responses only when they help reproduce a particular difference or support a useful offline check. Prepared, replay, and live results remain distinct; missing data must not silently select live access or sample content.

Report each current URL's comparison result, each fix's result, remaining differences, blocked checks, and the next action. Count deployed-verified cases separately from local-only cases. A family is complete only after all of its required variations are covered. Reopen a completed case if a later shared change produces a regression. The owner judges final acceptance and proposed intentional differences.

## Measure progress after each deployment

Follow [progress.md](progress.md). Before changing a selected URL, give its required functional and visual checks stable IDs and clear passing conditions. Keep those checks unchanged when comparing successive deployments. Record new requirements separately when source evidence establishes them; explain changes to the total rather than presenting them as regression or improvement.

Report completed URL cases and endpoint patterns, passing functional checks, passing visual checks, open differences, and blocked or unavailable checks separately. Show previous and current results, resolved differences, and regressions. Thirty implemented changes or fifteen verified improvements do not measure the fraction of the conversion completed. The thirty-eight scope rows group multiple endpoints, and the existing discovery cases still need to be matched to those endpoints before reporting an overall percentage.

For each run, retain the date, loaded revision, check definitions, matched comparison conditions, results, and evidence in the outer workspace. Use the same browser for each Rails/Django pair. Save paired screenshots and structured content/link/control observations when the supported tools allow it; record missing captures explicitly. Use the existing comparison tool's reports for supported repeatable checks, and documented browser controls for signed-in interactive checks. Do not copy browser authentication into scripts. A pixel difference requires review; do not widen tolerances just to pass. Manual visual confirmation remains required for every endpoint.

Work through the twenty selected URLs, making as many relevant improvements as reasonably possible and preferring to finish one URL before moving to another. Commit reasonable groups, push, and wait for the owner's deployment confirmation. Repeat every changed behavior and affected previously passing check. Keep unfinished URLs with concrete next actions, move whole completed URLs to the completed checklist, and refill the next list to twenty.

## Overall completion

The pending checklist includes the full endpoint scope, source and asset checks, repeatable offline checks, comparison coverage, and owner acceptance. Finish each required URL and variation with functional and visual evidence. Verify required real service connections and controlled failures, including homepage data and enabled/disabled challenge behavior. Preserve useful local replay without requiring a recording of every possible record or query.

Before final acceptance, run the agreed complete checks from a clean setup, account for unresolved or intentionally different behavior, and give the owner a coverage report and walkthrough. The owner explicitly accepts intentional differences and the replacement. Follow [the later cleanup review](../docs/future_branch_cleanup.md) only after acceptance and ordinary use provide a reason to retire conversion material.
