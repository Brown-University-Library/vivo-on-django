# Current batch: twenty URLs

Batch: url-batch-006, October 5, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). Fifteen unfinished URLs carry forward and five are added. Exact pairs are in `../../url_batch_006/urls.json` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_005_current_batch.md), [selected list](previous_workplan_artificts/url_batch_005_next_batch.md), and [evaluation](previous_workplan_artificts/url_batch_005_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `11fa230`; the loaded revision matches. Both preceding improvements pass. P01, P04, ABOUT01, HELP01, and FAQ01 complete their defined checks; P07 retains completion after the shared-script review. Six whole cases are now recorded. This does not complete their endpoint families or final owner acceptance.

Application commits `d031a63` and `7302dd3` contain the next search and homepage improvements. Local checks pass; these five outcomes await deployment and do not increase deployed pass totals. The tracking commit follows them. The private checkpoint records the final commit and confirmed push.

## Changes and deployed checks

| Change ID | Cases and change | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-006-01 | ADVANCED01, H01, EMPTY01, BROWSE01, SEARCH01, and shared forms: generate bare search and advanced-search paths while retaining slash aliases. | Both form aliases render; application-prefix tests pass. Local browser form action, Back to search, homepage search, and empty submission use the bare paths. | Confirm generated links/actions under the deployed prefix, both direct aliases, keyboard/pointer form submission, browser Back restoration, and affected profile/organization search controls. |
| url-batch-006-02 | Search and profile Advanced search links retain the current query string, including repeated filters and page. | Reference link and Rails include retain the query; rendered-link tests preserve repeated values and HTML escaping. Local browser navigation retains the complete decoded query. | Follow the link from EMPTY01, SEARCH01, filtered/paged search and any profile variation that exposes this link. Confirm path/query, field behavior, and browser return. |
| url-batch-006-03 | SEARCH01 and BROWSE01: long result titles keep 48 characters before the ellipsis in HTML and JSON, matching the reference. | Current common result and Rails presenter expose the one-character difference. Boundary tests cover short, exactly fifty-character, and longer Unicode titles in both representations. | Compare common long titles with Rails in desktop/narrow results and the supporting JSON. Short titles and full profile titles must remain correct. Keep count/order differences separate. |
| url-batch-006-04 | H01: expose the visible Search text as the button's accessible name. | Local browser identifies Search by its name and submits with Enter; the visible button is inspected. | Confirm the deployed button has the name Search and pointer/keyboard submissions reach the expected search query at both widths. |
| url-batch-006-05 | H01: active book-author links use bare public display paths and retain the application prefix. | Live/replay and mounted-prefix tests pass. The locally rendered book link has the correct path. | Follow a displayed book jacket; confirm the bare profile URL and correct author. Recheck settled Previous/Next wrap, the final short group, and visible image loading. |

## Local validation

- Full Django suite: 284 tests pass.
- Ruff lint and formatting: all six changed Python files pass.
- Pyright: all six changed Python files pass with zero errors/warnings using the project interpreter, Python 3.12, and basic checking. Pylance is unavailable. The already locked staging driver is installed in the local virtual environment so its import is checked.
- Local browser: matching advanced-form desktop/narrow appearance, named homepage Search button, bare search/author links, repeated-query navigation, keyboard submission, empty submission, and Back restoration pass using made-up data. These checks contact no application data service and do not certify deployment.
- All twenty-seven workplan Markdown files and 280 relative links/anchors pass validation. Twenty distinct selected URLs and all thirty-eight pending scope rows remain. `git diff --check` passes. Exact URLs, source data, PDFs, screenshots, and detailed logs remain outside Git.

## Remaining work

All twenty selected URLs retain specific remaining work in [next_batch.md](next_batch.md). New advanced/no-results/organization full views match, but shared navigation changes require deployed confirmation before moving these cases to completed. Default search differs in count/order; homepage has the same book count but a different order. The source queries match Rails, and alignment remains unconfirmed. The settled carousel boundary check passes; earlier observations taken during its transition are excluded.

Finish selected profile links, interactions, supporting assets, and full views. Retain organization membership differences and missing source variations. Every required endpoint eventually needs visual confirmation. The separate Manager remains excluded, and the earlier before-script source restriction remains in force.
