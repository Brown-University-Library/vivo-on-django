# Current batch: twenty URLs

Batch: url-batch-002, October 3, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). Twenty URLs carry forward; zero new URLs are added. Exact pairs remain in `../../url_batch_002/urls.json` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_001_current_batch.md) and [deployed evaluation](previous_workplan_artificts/url_batch_001_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed revision `6088911`; the loaded revision matches. Codex checked every preceding implemented outcome. Selected date and citation differences are resolved; all five sparse-profile bookmarks match. Search count/order and one organization member remain different. About and Help display the application's unavailable-page response in source modes.

Application commits `2bcfd77` (Affiliations spacing) and `c3c6ecc` (About/Help) contain the locally checked changes. The safe tracking commit follows them. The final handoff reports whether the push succeeds. The owner deploys after that confirmation; Codex then verifies each change below. Whole URLs completed remain zero.

## Changes and deployed checks

| Change ID | Cases and change | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-002-01 | All fifteen profiles: match the reference Affiliations heading's twenty-one-pixel bottom padding, correcting an eleven-pixel difference. | Reference computed styles and paired desktop/narrow profile captures establish the difference. Updated CSS also loads in local information-page comparisons. | Compare populated and empty Affiliations, plus View All, at desktop/narrow widths. Recheck the existing Publications heading rule. |
| url-batch-002-02 | ABOUT01/HELP01: enable the existing static handlers in live, replay, and prepared modes. | Both canonical and slash routes render actual templates in all three modes. An unrelated unconverted page remains unavailable. The local browser uses live mode without contacting a source for these pages. | Open both pages and confirm full content replaces the unavailable-page response; inspect shared assets. |
| url-batch-002-03 | ABOUT01/HELP01 and shared navigation: use the reference's bare About/Help paths while retaining older slash aliases. | Canonical reverses and both route forms pass; a mounted application retains its prefix. | Follow header/footer and cross-page links, checking direct rendering and application-prefix preservation. |
| url-batch-002-04 | ABOUT01/HELP01: load the reference presentation styles, match quotation marks and illustration descriptions, and keep the About inclusion-policy FAQ link within the application. | Full local content and heading positions match Rails at 1280×720 and 390×844. Illustrations load. Paired top/lower/footer captures differ by at most 0.07% of pixels. FAQ and Help links preserve a mounted prefix in tests. | Compare full content, illustrations, typography, wrapping, and footer at both sizes. Check the FAQ link and record any still-unconverted destination separately. |

## Local validation

- Full Django suite: 276 tests pass.
- Ruff lint and formatting: all four changed Python files pass.
- Pyright: all four changed Python files pass with zero errors/warnings using the project interpreter, Python 3.12, and basic checking. Pylance is unavailable.
- About/Help browser comparison: matching rendered text and heading positions at both widths; all observed images load. Inspected paired captures include the full content and footer. This is local evidence, not deployed completion.
- All sixteen workplan Markdown files and 213 relative links/anchors pass validation; `git diff --check` passes.
- The temporary local review server is stopped. Private records and screenshots remain outside Git.

## Remaining work

Keep all twenty cases in [next_batch.md](next_batch.md). Profiles still need full link, filter, asset, and visual coverage; P01 now has four of eight functional and four of twelve visual checks passing. Its remaining visual differences are recorded separately from the passing views.

Search count/order and the missing organization member require source alignment evidence; do not force counts, ordering, or membership to match one recorded snapshot. About/Help need deployed checks and still link to other unconverted information pages. The fourteen unavailable historical source variations and the rejected before-script check remain pending. Every required URL-pattern endpoint must eventually be visually confirmed against Rails.
