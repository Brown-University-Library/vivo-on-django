# Current batch: twenty URLs

Batch: url-batch-007, October 5, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). Seventeen unfinished URLs carry forward and three are added. Exact pairs are in `../../url_batch_007/urls.json` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_006_current_batch.md), [selected list](previous_workplan_artificts/url_batch_006_next_batch.md), and [evaluation](previous_workplan_artificts/url_batch_006_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `dedf2c8`; the loaded revision matches. Four preceding outcomes pass; the long-title outcome passes HTML but its supporting target JSON remains pending. ADVANCED01, EMPTY01 and O04 complete their defined checks, advancing whole cases from six to nine. Endpoint families and owner acceptance remain pending.

Two expanded-filter corrections are checked locally and await deployment. Application commit `2c8fab6` contains both fixes; a tracking commit follows it. The private checkpoint records the final commit and confirmed push after pushing. A push does not establish deployment or increase deployed pass totals.

## Changes and deployed checks

| Change ID | Cases and change | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-007-01 | SEARCH01 and BROWSE01 expanded filters: retain alphabetical ordering among tied counts when switching from A–Z to 9–0. Sort the maintained values before narrowing instead of sorting a new filtered copy. | Settled reference/target interaction demonstrates the difference. Local browser keyboard sorting retains tied order; paging, case-insensitive narrowing, page reset and empty results pass. | Open each applicable More dialog, switch A–Z then 9–0, compare tied entries with the reference, and repeat after narrowing and paging. Check keyboard controls and reopening. |
| url-batch-007-02 | SEARCH01 and BROWSE01 expanded filters: hide the empty loading-status paragraph so settled rows have the reference spacing. Keep nonempty loading and failure messages visible. | Settled deployed comparison shows the extra spacing. Local desktop/narrow views, async loading, displayed failure and successful retry pass; the empty status has zero height. | Compare settled first-row spacing at both widths. Observe loading and failure messages when applicable; successful retry must show rows and hide the cleared status. Recheck nearby controls and footer. |

## Local validation

- Full Django suite: 284 tests pass.
- JavaScript syntax check passes.
- Local browser: eight recorded filter outcomes pass using made-up records, including tied ordering, keyboard page navigation, narrowing, empty results, spacing, async loading, displayed failure and retry after reopening. Desktop/narrow views are inspected. These checks contact no application data service and do not certify deployment.
- No Python files change; changed-Python lint, formatting and type checks are not applicable.
- All thirty workplan Markdown files and 304 relative links/anchors pass validation. Twenty distinct selected URLs, all thirty-eight pending scope rows and `git diff --check` pass. Exact URLs, source data, screenshots and detailed logs remain outside Git.

## Remaining work

All twenty selected URLs retain specific work in [next_batch.md](next_batch.md). The preceding twenty URLs receive fresh complete baseline captures at both widths, with profile coverage limited to Overview. Finish the other profile sections, interactions, links and supporting documents. Source count/order, membership and book ordering remain different; source alignment is unconfirmed. Supporting JSON title confirmation is still pending.

Every required endpoint eventually needs visual confirmation. The separate Manager remains excluded. The earlier before-script source restriction remains in force; no HTML fetch or authentication-cookie extraction is used. Newly added information pages retain their earlier partial evidence and require the explicit checks in the next list.
