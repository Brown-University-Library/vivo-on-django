# Completion checks and retained definitions

These definitions keep comparisons consistent between releases. They were moved from [progress.md](progress.md) on October 6, 2026. Detailed current case results belong in [current_batch.md](current_batch.md), [checklist_completed.md](checklist_completed.md) and private evidence. The [case inventory](url_completion_inventory.md) holds whole-case state; the progress page holds the current global percentage.

Contents: [What to measure](#what-to-measure) · [Primary profile completion checks](#primary-profile-completion-checks)

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

The scope rows contain grouped endpoints. [url_completion_inventory.md](url_completion_inventory.md) explains the provisional case denominator and aliases; [checklist_completed.md](checklist_completed.md) retains whole-case evidence. Selected profiles, interactions and supporting formats still need reconciliation with complete endpoint coverage. Do not count screenshots, fragments, commits or individual fixes as additional completed cases.

## Primary profile completion checks

P01 originally completed these twenty checks. The table retains their definitions and recorded evidence; current whole-case state is in [the inventory](url_completion_inventory.md#cases). Preserve the definitions and historical evidence; publication variations belong to separate cases. Record newly demonstrated requirements separately. Each visual check includes the selected section, controls, heading, full relevant content, and footer. Match browser, viewport, loading state and scroll position between Rails and Django. Preserve paired evidence and record any missing capture.

| Check ID | Passing condition | Retained evidence |
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

The table preserves P01's original twenty definitions and their recorded evidence. Later demonstrated requirements remain additional checks, including SD06/F02a search/profile/Back/Forward history and SD17/F04a literal citation-link addresses where applicable. Keep their case assignments and deployed evidence in the shared-difference and case records. Moving this table does not retire those requirements, reset a passing check or establish a new pass.
