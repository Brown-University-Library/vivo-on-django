# Current batch: twenty URLs

Batch: url-batch-004, October 3, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). Nineteen URLs carry forward; FAQ01 is added. P07 moves to [completed](checklist_completed.md) under its fixed case checks. Exact pairs remain in `../../url_batch_004/urls.json` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_003_current_batch.md) and [deployed evaluation](previous_workplan_artificts/url_batch_003_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `a3bca98`; the loaded revision matches. Each of the three preceding changes passes its specified deployed outcome. Six supporting information pages and About/Help match full rendered content and inspected desktop/narrow layouts. Routes, navigation, and anchor checks pass. P07 completes five functional and ten visual checks. P01 now passes six of eight functional and six of twelve visual checks; its remaining differences drive the changes below.

The selected list has twenty distinct URLs. FAQ01's twelve in-page links have all been activated; full content and both-width appearance already match. Its remaining navigation/asset coverage stays explicit. Other incomplete URLs retain their concrete checks. This batch has no fixed improvement count.

Application commits `82a5701` restore ordinary profile text-link styles and `122b0a4` match research-area link spacing. These changes await deployment. The tracking commit follows them; the final handoff confirms whether all three commits have been pushed.

## Changes and deployed checks

| Change ID | Cases and change | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-004-01 | P01 and affected profiles: restrict the Overview text-link style to Overview. Research and other text panels retain their ordinary inherited font and panel link color. | Deployed comparison identifies smaller, heavier text links in the first scholarly-work item, which adds one desktop pixel and two narrow pixels below it. The stylesheet correction preserves the JavaScript section marker and table/Overview styles. Full tests and static checks pass. | Compare Research and View All links, fonts, first list-item height, following content, and footer at both widths. Recheck other text panels, section controls, Overview, and previously passing profile views. |
| url-batch-004-02 | P01 and profiles with research areas: preserve the reference whitespace inside each area link. | Source rendered links retain surrounding spaces. The generated HTML now retains them while preserving escaped labels, ordering, separators, and filter queries. Existing blank/malformed-entry regression coverage and the full suite pass. | Compare every research-area link's spacing, wrapping, and query in Overview/View All at both widths. Confirm labels remain escaped and links still reach the selected filtered search. |

## Local validation

- Full Django suite: 276 tests pass.
- Ruff lint and formatting: both changed Python files pass.
- Pyright: both changed Python files pass with zero errors/warnings using the project interpreter, Python 3.12, and basic checking. Pylance is unavailable.
- A temporary replay server starts with existing private recordings. Brave reports blocked navigation, and the server records missing recordings for the attempted exact requests. A local visual pass is not claimed. The temporary server is stopped; these changes require deployed visual comparison.
- All twenty-one workplan Markdown files and 242 relative links/anchors pass validation; twenty distinct selected cases and all thirty-eight pending scope rows remain. `git diff --check` passes. Private evidence remains outside Git.

## Remaining work

Repeat both corrections after deployment. Keep P01's complete CV/delivery and asset checks pending; its PDF's first page alone does not complete the document comparison. Repeat long narrow views through the footer, with completed image loading and enough capture frames. Finish ABOUT01/HELP01/FAQ01 remaining navigation/assets. Continue the other selected profile and organization cases; passed content/filter subsets do not certify whole URLs.

Bare About behavior and source count/order/membership differences stay open until explained. The previous before-script source restriction remains in force. Every required URL-pattern endpoint must eventually be visually confirmed against Rails before completion. Recheck P07 when a shared change affects it.
