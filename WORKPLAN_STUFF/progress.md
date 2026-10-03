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

Revision `e0cec5a`, evaluated October 3, 2026. Evidence label: `batch-001-profile-checks`. See the [batch evaluation](previous_workplan_artificts/batch_001_evaluation.md).

| Observation | Current result | Limit |
| --- | --- | --- |
| Whole URL cases certified in this workplan | 0 | Earlier work remains to be reconciled; this is not a claim that no pages are implemented. |
| First-batch improvements | 15 deployed verified; 14 lack qualifying examples; 1 before-script check blocked | All thirty passed local tests. These counts are not overall conversion progress. |
| Publication text on five selected profiles | 273 of 278 citation texts match Rails | Five chapter-collection spacing differences remain; the sample does not establish all publication coverage. |
| Primary profile section content | All six section states match rendered text | Other section appearance and supporting-link checks remain. |
| Primary profile appearance | Matched desktop and narrow Overview views checked, with narrow content below the first screen | This is partial visual coverage of the whole case; the other section views remain. |
| Other demonstrated differences | Sparse-profile View All and empty bookmarked sections differ | Keep those cases pending and plan focused fixes. |

Brave browser access was confirmed by reading the owner's signed-in staging homepage. Use its documented browser controls for ordinary page, interaction, and visual checks. Browser access does not supply absent source variations. The earlier page-source viewing rejection remains in force; do not use another browser to obtain that blocked result. The before-script condition remains pending until a permitted check is available.

## Primary profile completion checks

Use P01 as the next case to finish. It has no publications, so publication variations belong to separate cases. Start with these twenty checks; record newly demonstrated requirements separately. Each visual check includes the selected section, controls, heading, full relevant content, and footer. Match browser, viewport, loading state, and scroll position between Rails and Django. Preserve paired evidence and record any missing capture.

| Check ID | Passing condition | Current evidence |
| --- | --- | --- |
| P01-F01 | Every section and View All show the expected panels and matching rendered content. | Passed after deployment. |
| P01-F02 | A profile opened from the referring filtered search returns to that exact search, preserving repeated filters and its page. | Passed after deployment for the tested primary-profile journey. |
| P01-F03 | Direct entry after an unrelated search returns to default search. | Passed after deployment. |
| P01-F04 | Keyboard use selects each available section and exposes the expected active state. | Pending on P01; keyboard evidence from another profile does not complete this check. |
| P01-F05 | Internal content links, including institutions, organizations, and research areas, reach the expected destinations and retain required queries. | Pending complete coverage. |
| P01-F06 | External content links and the Manager link retain their required destinations; email links expose the expected address without sending mail. | Pending complete coverage; the desktop Manager link is visibly present. |
| P01-F07 | The linked CV opens the expected document and its required delivery checks pass. | Pending deployed comparison. |
| P01-F08 | Required images, fonts, styles, and scripts load; relevant browser errors or failed resources are explained. | Pending complete coverage; selected images loaded. |
| P01-V01 | Desktop Overview matches at 1280×720, including relevant content below the first screen. | Partial: matched initial view checked; complete capture remains. |
| P01-V02 | Desktop Research matches at 1280×720. | Pending visual comparison. |
| P01-V03 | Desktop Background matches at 1280×720. | Pending visual comparison. |
| P01-V04 | Desktop Affiliations matches at 1280×720. | Pending visual comparison. |
| P01-V05 | Desktop Teaching matches at 1280×720. | Pending visual comparison. |
| P01-V06 | Desktop View All matches at 1280×720. | Pending complete visual comparison. |
| P01-V07 | Narrow Overview matches at 390×844, including relevant content below the first screen. | Partial: matched top and lower views checked; preserve a complete evidence set for the case. |
| P01-V08 | Narrow Research matches at 390×844. | Pending visual comparison. |
| P01-V09 | Narrow Background matches at 390×844. | Pending visual comparison. |
| P01-V10 | Narrow Affiliations matches at 390×844. | Pending visual comparison. |
| P01-V11 | Narrow Teaching matches at 390×844. | Pending visual comparison. |
| P01-V12 | Narrow View All matches at 390×844. | Pending visual comparison. |

Starting results under this explicitly defined checklist: functional checks 3/8 passed; visual checks 0/12 complete, with two partial views; whole case pending. These stricter whole-case criteria do not erase the observed Overview matches or change the fifteen verified batch improvements. They expose what remains before calling the URL complete.

## Run the next iteration

1. Codex matches the approved endpoint scope to the existing cases and records which patterns or variations still lack a case. Preserve discovery IDs and keep the private URL bindings outside Git. Do not delay P01's already defined comparisons while reconciling other families.
2. Codex finishes the twenty P01 checks, preserving each result and the exact loaded revision. Use supported Brave or in-app browser controls for authenticated comparisons. Use response checks for supporting formats and inspect their relevant displayed page or artifact visually as required. Separate changing source data from a demonstrated application difference.
3. Codex records every planned outcome as passed, different, blocked, unavailable, partial, or not run, with evidence and the next action. An evaluation pass ends when those outcomes are recorded; the URL stays pending until its completion conditions pass. Carry absent citation edge cases forward without repeatedly searching or inventing live examples.
4. Codex fixes demonstrated differences, preferring to finish P01. A batch may contain fewer than thirty changes. Run the required local checks, commit and push the implementation batch under the established authorization, and tell the owner it is ready to deploy.
5. The owner deploys and confirms completion. Codex verifies the loaded revision, repeats the same affected checks, and checks relevant previously passing cases for regressions. Keep Rails/Django screenshot pairs close in time and under matching conditions.
6. Codex reports the prior and current totals, exactly which checks now pass, resolved differences, regressions, and remaining limits. Mark completed URL cases and endpoint patterns separately. Continue with the next case when the current one is complete or a recorded dependency prevents useful progress. Owner acceptance of differences and final site acceptance remain separate decisions.

For repeatable supported comparisons, reuse the existing [comparison command and guide](../docs/conversion/browser_comparison.md), which produce structured observations, paired screenshots, and pixel-difference reports. The existing command has limits and does not establish signed-in deployed access on its own. Use documented browser controls where needed. Do not bypass a rejected browser action or copy authentication cookies into helpers.

Implementation update, October 3, 2026: batch-002 addresses the three demonstrated outcomes in [current_batch.md](current_batch.md). The selected saved citation comparison now matches 278/278 texts locally; the broader saved sample has 25 remaining differences, down from 39. These are local results and do not change deployed totals. P01 remains at 3/8 functional checks and 0/12 complete visual checks, with two partial views. The latest browser attempt was blocked by an open extension interface after sign-in; resume its remaining checks when automation is available.
