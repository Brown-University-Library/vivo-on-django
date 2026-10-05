# Measure progress toward the public-site replacement

Started October 3, 2026. Follow [workplan.md](workplan.md) and [GOAL.md](GOAL.md). This record defines how Codex and the owner measure successive deployed comparisons. It does not certify historical work or owner acceptance. Exact URLs, records, screenshots, and detailed results stay in the outer workspace.

Contents:

- [What to measure](#what-to-measure)
- [Current evidence](#current-evidence)
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

The thirty-eight scope rows contain grouped endpoints. The existing external discovery manifest has sixty-two case specifications, and the current review added eight publication variations outside that manifest. Match the actual endpoint patterns and required cases before establishing an overall denominator. These counts do not establish the percentage of the site completed.

## Current evidence

Revision `dedf2c8`, evaluated October 5, 2026. See the [sixth URL-batch evaluation](previous_workplan_artificts/url_batch_006_evaluation.md). Earlier improvement-count evaluations remain historical evidence.

| Observation | Current result | Limit |
| --- | --- | --- |
| Whole URL cases certified in this workplan | 9 (P01, P04, P07, ABOUT01, HELP01, FAQ01, ADVANCED01, EMPTY01, O04) | Partial comparisons do not certify a whole URL. |
| First improvement-count batch | 15 deployed verified; 14 lack qualifying examples; 1 before-script check blocked | Keep these states distinct from local tests. |
| Publication text and inline elements on the original five profiles | Previous full comparison: 278/278 match Rails | Preserved evidence; current selected filter checks also compare visible citation text. |
| Publication filter states | 35/35 match selected control and visible ordered citations | Ten profiles checked with keyboard selection; full visual/link checks remain separate. |
| Expanded twenty-URL citation sample | Previous full comparison: 345/345 texts and inline-element sequences match | Current filter checks pass; full visual/link checks remain pending. |
| Profile content and conditional buttons | All 15 selected profiles match the compared section text and button lists | This does not establish full links, interactions, assets, or visual coverage. |
| Sparse-profile fresh bookmarks | 5/5 match Rails | P07 passes all five functional and ten visual criteria after settled capture and asset checks. |
| Shared asset content versions | Present on profiles and About/Help | All observed information-page illustrations load. P07 asset evidence passes; font delivery and byte comparisons explain the export-tool limitation. Other case audits remain pending. |
| Primary profile completion checks | 8/8 functional passed; 12/12 visual passed | Complete CV bytes, all eleven pages, signed-in delivery behavior, Overview navigation and complete section views pass. Other profile variations remain pending. |
| Search and organization content | Previously observed count/order and missing-member differences remain open | Fresh complete desktop/narrow baselines inspected; source alignment is unconfirmed. |
| Information pages | About/Help/FAQ complete their defined functional and visual checks | Both observed About aliases and every FAQ anchor are confirmed. Five supporting pages retain whole-case checks. |
| Search/homepage deployment outcomes | 4/5 complete; long-title HTML passes but JSON is pending | Supporting JSON requires permitted signed-in confirmation. |
| Newly completed cases | ADVANCED01, EMPTY01 and O04 each pass 4/4 functional and 2/2 visual checks | These criteria are now explicit; they do not imply an increase on an earlier undefined denominator. |
| Fresh preceding-batch baseline | 20 URLs, 40 desktop/narrow pairs, 289 frames through all footers | Profile coverage is Overview only; other states remain pending. |
| Current URL-based batch | 20 distinct URLs: 17 carried forward, 3 added | Three cases complete this review; two expanded-filter corrections await deployment. See `next_batch.md`. |

Measure the same checks before and after deployment. Use content versions on changed assets to avoid reusing older browser resources; verify the requested version and rendered behavior rather than assuming refresh succeeded. Source count/order differences stay open until explained and checked.

Brave browser access was confirmed by reading the owner's signed-in staging homepage. Use its documented browser controls for ordinary page, interaction, and visual checks. Browser access does not supply absent source variations. The earlier page-source viewing rejection remains in force; do not use another browser to obtain that blocked result. The before-script condition remains pending until a permitted check is available.

## Primary profile completion checks

Use P01 as the next case to finish. It has no publications, so publication variations belong to separate cases. Start with these twenty checks; record newly demonstrated requirements separately. Each visual check includes the selected section, controls, heading, full relevant content, and footer. Match browser, viewport, loading state, and scroll position between Rails and Django. Preserve paired evidence and record any missing capture.

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
3. Codex runs required local checks, commits reasonable groups, pushes, and tells the owner the code is ready. The owner deploys and confirms completion.
4. Codex verifies the loaded revision and each recorded improvement, then records all required checks for the twenty URLs as passed, different, blocked, unavailable, partial, or not run. Compare desktop/narrow views and relevant lower content under matching conditions. Keep source-data differences distinct from application differences.
5. Codex reports prior/current totals on the same checks, resolved differences, and regressions. Move only whole completed URLs to [checklist_completed.md](checklist_completed.md). Keep unfinished URLs with specific next actions and add pending URLs to refill the next list to twenty. Report how many carry forward and how many are added, then continue the work.

For repeatable supported comparisons, reuse the existing [comparison command and guide](../docs/conversion/browser_comparison.md), which produce structured observations, paired screenshots, and pixel-difference reports. The existing command has limits and does not establish signed-in deployed access on its own. Use documented browser controls where needed. Do not bypass a rejected browser action or copy authentication cookies into helpers.

Current results on the same P01 checklist: functional checks 8/8 passed; visual checks 12/12 passed; whole case complete. Four preceding search/homepage outcomes pass on `dedf2c8`; the fifth passes HTML but its JSON portion is pending. The two new expanded-filter corrections in [current_batch.md](current_batch.md) are checked locally and await deployment; they do not add deployed passes.

The settled capture method limits native wheel movement to the remaining page height. Excess movement produces elastic overscroll and misleading white bands. Observe completed image loading and record whether long captures actually reach the footer; a fixed frame limit is not full-page evidence.
