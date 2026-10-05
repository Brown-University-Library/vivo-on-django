# Measure progress toward the public-site replacement

Started October 3, 2026. Follow [workplan.md](workplan.md) and [GOAL.md](GOAL.md). This record defines how Codex and the owner measure successive deployed comparisons. It does not certify historical work or owner acceptance. Exact URLs, records, screenshots, and detailed results stay in the outer workspace.

**Estimated URL-case completion: 20.8% — 16 of 77 known cases complete.** This is the provisional case-based estimate requested for an at-a-glance view. It counts completed cases, not implementation effort or final acceptance. The [named inventory](url_completion_inventory.md) shows the denominator, merged aliases and completed cases. Some discovery entries still need reconciliation with the endpoint scope; explain additions or merges when the estimate changes.

Snapshot: October 5, 2026 at 14:10 America/New_York, verification checkpoint. Completion is 16/77 (20.8%); the provisional denominator is unchanged. E01 completes after the layout correction on loaded `95a4f65`. P08 confirms five functional and fourteen visual criteria; the document error-response difference remains for review. Institution fallback passes; illustration delivery and the remote collected-file command remain pending. The fixed run cutoff is October 6, 2026 at 08:00 America/New_York (12:00 UTC).

Contents:

- [What to measure](#what-to-measure)
- [Current evidence](#current-evidence)
- [Six-hour snapshots](#six-hour-snapshots)
- [Primary profile completion checks](#primary-profile-completion-checks)
- [Run the next iteration](#run-the-next-iteration)

## What to measure

The main measure is completed required URL cases and endpoint patterns. An endpoint passes only when all its required variations have functional and visual evidence, or the owner explicitly accepts a documented difference. Every required URL-pattern endpoint must eventually receive visual confirmation against Rails. A partially checked page is not complete.

Keep separate totals for:

| Measure | Meaning |
| --- | --- |
| Completed URL cases / required cases | Whole cases with all required checks satisfied. |
| Completed endpoint patterns / required patterns | Endpoint patterns whose required cases are complete. |
| Passing deployed functional checks / defined functional checks | Matching content, controls, navigation, response formats, and supporting links. |
| Passing visual checks / defined visual checks | Matching views at the specified size and state, including relevant content below the first screen. |
| Open differences | Known mismatches, identified separately so repeated observations do not inflate the count. |
| Blocked, unavailable, partial, and not-yet-run checks | Checks with insufficient evidence; none count as passing. |
| Changes since the previous deployment | Newly passing checks, resolved differences, and regressions on the same defined checks. |

Use stable IDs for scope rows, URL cases, and individual checks. Scope IDs and discovery case IDs are different fields; some use the same letters and numbers. Before each implementation batch, fix the selected case's passing conditions. Preserve them across deployments. Record newly discovered requirements and changes to the number of checks separately. Do not report one percentage combining local tests, implemented fixes, deployed behavior, and visual coverage.

The thirty-eight scope rows contain grouped endpoints. For the provisional estimate, [url_completion_inventory.md](url_completion_inventory.md) combines sixty-two original discovery specifications with twenty later case names, then merges five known aliases, yielding seventy-seven named cases. The sixteen completed cases have whole-case evidence in `checklist_completed.md`; all other entries remain pending. The additions include eight publication-profile cases and seven additional information pages after alias reconciliation. This is a useful rough URL-case measure while the remaining interaction and format entries are reconciled with scope, not a precise estimate of engineering time. Do not count screenshots, fragments, commits or individual fixes as additional completed cases.

## Current evidence

Current daily-run evidence includes loaded `95a4f65`, evaluated October 5, 2026; preceding evidence remains on `88fb8e4`. See the [seventh URL-batch evaluation](previous_workplan_artificts/url_batch_007_evaluation.md). Earlier improvement-count evaluations remain historical evidence.

| Observation | Current result | Limit |
| --- | --- | --- |
| Whole URL cases certified in this workplan | 16 (P01, P03, P04, P07, ABOUT01, HELP01, FAQ01, ADVANCED01, EMPTY01, O04, TERMS01, HISTORY01, HELP_VIZ01, ROADMAP01, PUBLICATIONS01, E01) | Partial comparisons do not certify a whole URL. |
| First improvement-count batch | 15 deployed verified; 14 lack qualifying examples; 1 before-script check blocked | Keep these states distinct from local tests. |
| Publication text and inline elements on the original five profiles | Previous full comparison: 278/278 match Rails | Preserved evidence; current selected filter checks also compare visible citation text. |
| Publication filter states | 35/35 match selected control and visible ordered citations | Ten profiles checked with keyboard selection; full visual/link checks remain separate. |
| Expanded twenty-URL citation sample | Previous full comparison: 345/345 texts and inline-element sequences match | Current filter checks pass; full visual/link checks remain pending. |
| Profile content and conditional buttons | All 15 selected profiles match the compared section text and button lists | This does not establish full links, interactions, assets, or visual coverage. |
| Sparse-profile fresh bookmarks | 5/5 match Rails | P07 passes all five functional and ten visual criteria after settled capture and asset checks. |
| Shared asset content versions | Present on profiles and About/Help | All observed information-page illustrations load. P07 asset evidence passes; font delivery and byte comparisons explain the export-tool limitation. Other case audits remain pending. |
| Primary profile completion checks | 8/8 functional passed; 12/12 visual passed | Complete CV bytes, all eleven pages, signed-in delivery behavior, Overview navigation and complete section views pass. Other profile variations remain pending. |
| Search and organization content | Previously observed count/order and missing-member differences remain open | Fresh complete desktop/narrow baselines inspected; source alignment is unconfirmed. |
| Information pages | All eight information pages complete their defined functional and visual checks | Both observed About aliases and every FAQ anchor are confirmed. The separate institution page remains pending. |
| Search/homepage deployment outcomes | 5/5 complete; long-title HTML and signed-in JSON pass | Permitted read-only Console checks confirm keyword and browse titles. |
| Cases completed during the preceding review | ADVANCED01, EMPTY01 and O04 each pass 4/4 functional and 2/2 visual checks | These criteria are now explicit; they do not imply an increase on an earlier undefined denominator. |
| Fresh preceding-batch baseline | 20 URLs, 40 desktop/narrow pairs, 289 frames through all footers | Profile coverage is Overview only; other states remain pending. |
| P03 completion evidence | 6/6 functional criteria pass; 12/12 complete visual views pass | Filtered/paged return, CV bytes, all five rendered pages and signed-in delivery pass; the selected whole case completes. |
| Expanded-filter deployment outcomes | 2/2 corrected outcomes pass | All applicable named dialogs match tie ordering and 15-pixel settled first-row spacing at both widths. Search source-data differences remain open. |
| P08 daily-run evidence | 5/6 functional criteria and 14/14 complete visual states pass | Complete CV bytes/pages, HEAD and valid range agree; unsatisfied-range error metadata remains for review. Whole case pending. |
| Current URL-based batch | 20 distinct URLs: 16 carried forward, 4 added | Six cases complete this review. Both filter fixes and the remaining supporting title check pass. Institution rendering/fallback and missing-record layout pass; the remote collected-file command and illustration delivery remain pending. E01 completes and L03 fills its slot. See `next_batch.md`. |

Measure the same checks before and after deployment. Use content versions on changed assets to avoid reusing older browser resources; verify actual served bytes and rendered behavior rather than assuming the requested version proves delivery. Confirm collected copies during deployment, then refresh without cached resources when the browser still uses older bytes. Source count/order differences stay open until explained and checked.

Brave browser access was confirmed by reading the owner's signed-in staging homepage. Use its documented browser controls for ordinary page, interaction, and visual checks. Browser access does not supply absent source variations. The earlier page-source viewing rejection remains in force; do not use another browser to obtain that blocked result. The before-script condition remains pending until a permitted check is available.

## Six-hour snapshots

During active improvement work, use `America/New_York` boundaries at 00:00, 06:00, 12:00 and 18:00. Update at the first suitable checkpoint after a boundary; do not interrupt a browser interaction just to hit an exact minute. Also update at daily start, resumption and final handoff. If several boundaries pass during an interruption, write one honest current snapshot when work resumes rather than invent historical results. No separate scheduled task runs while the chat is idle.

1. Read the completed checklist and pending/regression records. Update the named inventory's whole-case states; retained passes need their existing evidence, and reopen a case when a regression invalidates completion.
2. Count completed canonical case IDs once, divide by the total named inventory, and show the fraction and percentage at the top of this file. Keep local-only, blocked, partial and unverified cases in the denominator. Preserve the alias map; record any additions, merges or exclusions and their reasons. Do not reduce the denominator merely because evidence is difficult to obtain.
3. Record the snapshot time, latest verified revision, latest pending release, resolved differences, regressions, blocked checks and exact next action. Keep detailed results private. If nothing passed since the preceding snapshot, retain the same percentage and say so. An unchanged snapshot is still useful confirmation.
4. Add a concise history row below. Update the last-snapshot time and next six-hour boundary in `../../ongoing_run.local.md`. Group safe tracking commits with normal release/pass records when authorized; do not trigger a deployment solely to satisfy every clock boundary.

| Snapshot | Completed / known cases | Estimated completion | Verified evidence / remaining limit |
| --- | --- | --- | --- |
| October 5, 2026 — workflow update | 15 / 77 | 19.5% | Existing whole-case evidence through `88fb8e4`; `f40c0dd` requires verification. Inventory v1 is provisional; no new deployed checks run during this update. |
| October 5, 2026 at 12:43 America/New_York — daily start | 15 / 77 | 19.5% | Denominator unchanged. Loaded `aae7a67` includes pending changes; per-change checks begin. No new whole case passes at start. |

| October 5, 2026 at 14:10 America/New_York — verification checkpoint | 16 / 77 | 20.8% | E01 completes on `95a4f65`; denominator unchanged. P08 retains the document error-response review. Next scheduled boundary remains 18:00 local. |

The estimate can decrease when scope gains required cases or a regression reopens a case. Explain that change instead of hiding it. A later estimate of work remaining may be added separately with its basis and uncertainty; it must not replace or silently change this measured fraction. Complete endpoint coverage, integration checks and owner acceptance remain separate requirements even if all currently named cases pass.

## Primary profile completion checks

P01 is complete under these original twenty checks. Preserve their definitions and historical evidence; publication variations belong to separate cases. Record newly demonstrated requirements separately. Each visual check includes the selected section, controls, heading, full relevant content, and footer. Match browser, viewport, loading state and scroll position between Rails and Django. Preserve paired evidence and record any missing capture.

| Check ID | Passing condition | Current evidence |
| --- | --- | --- |
| P01-F01 | Every section and View All show the expected panels and matching rendered content. | Passed after deployment. |
| P01-F02 | A profile opened from the referring filtered search returns to that exact search, preserving repeated filters and its page. | Passed after deployment for the tested primary-profile journey. |
| P01-F03 | Direct entry after an unrelated search returns to default search. | Passed after deployment. |
| P01-F04 | Keyboard use selects each available section and exposes the expected active state. | Passed on P01 at desktop/narrow widths; each available section and View All exposes the expected panels and selected control. |
| P01-F05 | Internal content links, including institutions, organizations, and research areas, reach the expected destinations and retain required queries. | Passed on `a3bca98`: all seven internal content links reach their expected paths and queries. |
| P01-F06 | External content links and the Manager link retain their required destinations; email links expose the expected address without sending mail. | Passed on `a3bca98`: external/email hrefs match and the Manager retains its configured destination. |
| P01-F07 | The linked CV opens the expected document and its required delivery checks pass. | Passed on `11fa230`: complete matching bytes, all eleven rendered pages, and signed-in delivery checks. |
| P01-F08 | Required images, fonts, styles, and scripts load; relevant browser errors or failed resources are explained. | Passed on `ee0c95f` and retained on `11fa230`: complete browser image loading, required asset delivery and matching bundled font bytes, with no relevant warnings/errors. Protected-image metadata redirects alone are not failures or delivery proof. |
| P01-V01 | Desktop Overview matches at 1280×720, including relevant content below the first screen. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V02 | Desktop Research matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V03 | Desktop Background matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V04 | Desktop Affiliations matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V05 | Desktop Teaching matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V06 | Desktop View All matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V07 | Narrow Overview matches at 390×844, including relevant content below the first screen. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V08 | Narrow Research matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V09 | Narrow Background matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V10 | Narrow Affiliations matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V11 | Narrow Teaching matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V12 | Narrow View All matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |

Starting results under this explicitly defined checklist: functional checks 3/8 passed; visual checks 0/12 complete, with two partial views; whole case pending. These stricter whole-case criteria do not erase the observed Overview matches or change the fifteen verified batch improvements. They expose what remains before calling the URL complete.

P04 preserves five original functional and ten visual conditions, plus the separately added institution requirement. On `11fa230`, all five original functional, all ten visual, and the added requirement pass. The configured Manager value is echoed consistently on homepage/profile; local environment differences are not deployed failure evidence. The whole selected case completes. About/Help/FAQ each pass four defined functional and two complete visual checks. These newly explicit information-page denominators do not imply an increase on an older undefined count.

## Run the next iteration

1. Codex records the twenty selected URLs, their fixed passing conditions, current evidence, and specific remaining work in [next_batch.md](next_batch.md). Preserve stable case IDs and private URL bindings. Reconcile endpoint coverage while continuing useful work on selected URLs.
2. Codex reviews each URL and makes as many relevant improvements as reasonably possible, preferring to finish an individual URL. Record per-change expected outcomes in [current_batch.md](current_batch.md). Missing source variations remain pending without repeated searches for examples.
3. Codex runs required local checks and releases reasonable groups when the owner's current prompt authorizes commits/pushes. The scheduled caller deploys; Codex follows [automatic deployment checks](workplan.md#automatic-deployment-and-verification), including loaded revision and actual asset delivery. Continue without waiting for owner confirmation; do not push another release until the preceding release's verification is accounted for.
4. Codex verifies every recorded change and affected previously passing behavior after each release. At the pass boundary, account for all selected URLs and required checks as passed, different, blocked, unavailable, partial or not run. Retain applicable earlier evidence for unchanged checks with its revision and reason. Compare desktop/narrow views and relevant lower content under matching conditions. Keep source-data differences separate.
5. Codex reports prior/current totals, resolved differences and regressions. Complete only whole verified URLs, update [the inventory](url_completion_inventory.md), and carry unfinished URLs with concrete actions. Refill and begin another pass only before the fixed daily cutoff. At the cutoff, finish the active pass and handoff. Refresh the completion snapshot using the procedure above.

For repeatable supported comparisons, reuse the existing [comparison command and guide](../docs/conversion/browser_comparison.md), which produce structured observations, paired screenshots, and pixel-difference reports. The existing command has limits and does not establish signed-in deployed access on its own. Use documented browser controls where needed. Do not bypass a rejected browser action or copy authentication cookies into helpers.

Current results on the same P01 checklist: functional checks 8/8 passed; visual checks 12/12 passed; whole case complete. Four preceding search/homepage outcomes pass on `dedf2c8`; the fifth now also passes supporting JSON on `88fb8e4`. Both expanded-filter corrections pass after collection and browser refresh. The institution fallback and missing-record wrapper corrections in [current_batch.md](current_batch.md) pass deployed checks; illustration delivery and the remote collected-file command remain pending.

The settled capture method limits native wheel movement to the remaining page height. Excess movement produces elastic overscroll and misleading white bands. Observe completed image loading and record whether long captures actually reach the footer; a fixed frame limit is not full-page evidence.

October 5, 2026 at 13:19 America/New_York: E01 completes four functional and two complete visual criteria on loaded `95a4f65`, confirmed again after comparison. Whole cases advance to 16/77 (20.8%); denominator unchanged. Institution fallback placement also passes, but illustration delivery remains unavailable. The remote collected-file command is not run; served bytes pass. Next scheduled snapshot remains 18:00 local time.
