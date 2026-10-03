# Current batch: twenty URLs

Follow [workplan.md](workplan.md) and [../AGENTS.md](../AGENTS.md). [next_batch.md](next_batch.md) lists the twenty selected URLs and their specific remaining work. Exact URL pairs remain in `../../current_urls.local.md` and `../../url_batch_001/urls.json`, outside Git. Private evidence label: `url-batch-001-checks`. The preceding [implementation record](previous_workplan_artificts/batch_002_current_batch.md) and [deployed evaluation](previous_workplan_artificts/batch_002_evaluation.md) are archived.

Contents:

- [Status and review coverage](#status-and-review-coverage)
- [Implemented changes and required deployed checks](#implemented-changes-and-required-deployed-checks)
- [Local validation](#local-validation)
- [Remaining URL work](#remaining-url-work)
- [Deployment and next list](#deployment-and-next-list)

## Status and review coverage

- Batch: url-batch-001, October 3, 2026; the first batch under the twenty-URL workflow.
- Selection: twenty distinct URLs, eleven carried forward from recent profile batches and nine added to this active list. Older evidence exists for some added URLs.
- Starting branch/revision: `main` / `2ba9b1f`; owner-confirmed deployment and the loaded revision match.
- State: awaiting owner deployment after Codex confirms the push. Implementation, local checks, and application commits are complete; deployed checks remain pending.
- Application commits: `fc42808` (citation/date/search matching) and `48c26cc` (asset content versions).
- Push result: the final handoff confirms whether these commits and this tracking record reached the remote; the detailed Git result stays in the private checkpoint.
- Whole selected URLs complete: zero. Local tests and partial browser comparisons do not certify whole URLs.

Compared rendered section text, conditional buttons, available citation text/inline elements, and observed images on fifteen profiles. All fifteen conditional-button lists match; 342/345 citation texts and 344/345 inline-element sequences match before this batch. The three text differences are addressed locally; keep this expanded baseline separate from the prior 278-citation sample. Compared two organizations and one search. No observed broken images were found in those eighteen pages, but a complete asset audit is still required. Browser access to About and Help was blocked by a client error; the owner has been asked to make those pages load. These are partial reviews, not full interaction, link, or desktop/narrow coverage.

The preceding batch's 278 selected citation texts and inline elements now match Rails after deployment. Required empty panels exist and conditional controls match; a View All check has partial matching evidence. Fresh empty-section and View All bookmarks still differ in the reviewed browser even though the server supplies the changed script. Asset versioning addresses a possible stale-script cause; only another deployed check can establish whether it resolves the difference.

## Implemented changes and required deployed checks

| Change ID | URL cases and implementation | Local result | Required deployed check |
| --- | --- | --- | --- |
| url-batch-001-01 | P10/P11 and affected profiles: keep the hyphen in date ranges when the start, end, or both dates are absent. Apply the same rule to appointments, credentials, and training. | Date-range and rendered-row regressions pass, including invalid dates and future end years. | Compare P10's undated credential and P11's open appointment with Rails; inspect applicable rows on all selected profiles. |
| url-batch-001-02 | P13 and affected publication profiles: preserve source spacing inside italic book titles and collections, while whitespace-only values remain absent. | Book spacing and existing chapter spacing regressions pass. | Compare P13 citation row 5 text and inline elements; recheck all 278 selected citations and full Publications views. |
| url-batch-001-03 | P06/P14 and affected publication profiles: retain the closing curly title quote inside the reference formatter's straight quotes. | Ordinary and nested quote regressions pass; saved reference comparison improves without new differences. | Compare P06 row 0 and P14 row 6 text and inline elements, and check other affected titles and publication filters. |
| url-batch-001-04 | All twenty selected URLs: add a content version to shared stylesheet/script URLs. Profile tabs, search controls, and organization styles also receive their own versions. | Changed contents produce a new address; unchanged contents reuse it. Configured URL prefixes, query values, fragments, and missing-asset addresses are preserved. A local Brave profile loads the versioned assets and selects empty Teaching/All bookmarks correctly without their buttons. | Confirm deployed pages request versioned resources. Reload fresh P04 Affiliations and P07 Background/Affiliations/Teaching/All bookmarks, compare visible panels with Rails, and check normal controls, keyboard use, and affected page assets. |
| url-batch-001-05 | SEARCH01: use Rails' all-term query operator and the source server's configured parser rather than explicitly choosing another parser. | Request and search rendering regressions pass for ordinary, combined, filtered, paged, and empty searches. Rails source establishes these options. | Compare result count/order, facets, highlighting, filter removal, pagination, and keyboard use. Underlying source alignment is still unconfirmed; do not assume this change resolves all content differences. |

## Local validation

- Full Django suite: 273 tests pass, up from 267 before this batch.
- Ruff lint and formatting: all nine changed Python files pass.
- Pyright: all nine changed Python files pass with zero errors/warnings using the project interpreter and basic checking. Pylance is unavailable.
- Saved reference comparison: 3,808 citations, 25 text differences before these changes and 2 afterward; 23 newly matching, zero regressions. The two remaining differences involve Unicode whitespace in other saved source cases. This is local evidence, not a deployed pass.
- JavaScript section checks: thirteen initial-section cases and return-to-Overview interactions pass using the actual script.
- Local Brave check: versioned shared assets and the section script load; an empty Teaching bookmark displays Teaching, View All displays all four panels without an All button, and Overview returns to the ordinary panel. The made-up profile's images load. This does not certify live profiles or matched Rails appearance. A screenshot was inspected in the browser tool; a saved paired capture is not available for this local check.
- Existing source request recordings made with earlier search options need fresh compatible recordings for the changed search request. No automatic live fallback or sample substitution was added.
- Private URL bindings, source records, and browser observations remain outside Git. Tracked examples use made-up names and records.

## Remaining URL work

[next_batch.md](next_batch.md) records a specific result and next action for every URL. Profile cases need complete link, filter, keyboard, supporting-asset, and desktop/narrow comparisons; preserve P01's fixed twenty checks in [progress.md](progress.md). Sparse-profile bookmarks need another deployed check. The organization comparison has one missing reference member; source access from the workstation did not succeed, so its cause remains unconfirmed. Search count/order remain different pending the query update and source alignment checks. About and Help need usable browser access before their full deployed review.

Carry the first improvement-count batch's fourteen unavailable real-source variations and blocked before-script check forward. Do not obtain the previously rejected page-source result through another browser or tool. No URL is moved to completed solely because all available checks have been attempted. Every required URL-pattern endpoint must eventually be confirmed visually against Rails.

## Deployment and next list

1. Codex reviews and commits related application changes in reasonable groups, then commits the safe workflow/evaluation records and confirms the push. Tell the owner the code is ready.
2. The owner deploys the latest pushed `main` and reports completion.
3. Codex verifies the loaded revision and checks every implemented change above, then completes or records every selected URL's remaining checks. Keep functional and visual results distinct.
4. Move whole completed URLs to [checklist_completed.md](checklist_completed.md). Retain unfinished URLs in `next_batch.md` with specific next actions, add pending URLs to refill the list to twenty, and report carried/new counts. Continue the work after announcing the list.
