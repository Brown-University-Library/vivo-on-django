# Current batch: twenty URLs

Batch: url-batch-003, October 3, 2026. Follow [workplan.md](../workplan.md), [next_batch.md](../next_batch.md), and [../AGENTS.md](../../AGENTS.md). Twenty URLs carry forward; zero new URLs are added. Exact pairs remain in `../../../url_batch_003/urls.json` and `../../../current_urls.local.md`, outside Git. The preceding [implementation](url_batch_002_current_batch.md) and [deployed evaluation](url_batch_002_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed revision `98cf271`; the loaded revision matches. Codex checked each preceding change. Profile heading spacing and About/Help rendering/content/appearance pass the selected checks. Bare About still ends at a slash URL in Brave, so its direct path behavior remains pending. Thirty-five publication filter states match. P01 now has four of eight functional and six of twelve visual checks passing. No whole URL is certified yet.

The changes below repair information destinations needed by ABOUT01, HELP01, and shared navigation. These supporting pages do not add six selected URLs to the twenty-case batch or establish standalone endpoint completion. The final handoff reports the tested commits and confirmed push; the owner deploys after that confirmation.

Application commits `3672e4f` restore information-page content and `eb3e62d` enable public routes in source modes. The safe tracking commit follows them.

## Changes and deployed checks

| Change ID | Cases and change | Local check results | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-003-01 | ABOUT01/HELP01 and shared navigation: enable FAQ, History, Roadmap, publication help, Terms of Use, and visualization help in live, replay, and prepared modes. | All six handlers render real templates in each mode without source access. Unrelated unconverted pages remain unavailable. | Follow About/Help and footer links. Confirm all six destinations render full pages, including existing illustrations and shared presentation. |
| url-batch-003-02 | Use the reference's bare public paths for these six destinations, retaining slash aliases. Keep the Roadmap visualization-help link inside a mounted application. | Canonical reverses, both path forms, and mounted About/Help/Roadmap navigation pass tests. | Follow each actual link; verify expected paths, fragments, and application prefix. Recheck bare About behavior separately. |
| url-batch-003-03 | Restore reference text, punctuation, lists, headings, anchors, illustrations, and spacing on the six supporting information pages. | Full rendered text matches at desktop/narrow widths. Forty paired screenshot frames match at the measured pixel threshold and were visually inspected. FAQ's twelve in-page links and publication help's six links have targets; sampled clicks reach the final sections. Existing generic sample-illustration text and new-tab link protection are retained. | Repeat complete content and desktop/narrow visual comparisons. Check FAQ and publication-help anchors, Roadmap's link, observed images, and required assets. Record any difference instead of counting local check results as deployed completion. |

## Local validation

- Full Django suite: 276 tests pass.
- Ruff lint and formatting: all four changed Python files pass.
- Pyright: all four changed Python files pass with zero errors/warnings using the project interpreter, Python 3.12, and basic checking. Pylance is unavailable.
- Six supporting pages: matching rendered text and paired full-content/footer screenshots at 1280×720 and 390×844. Forty measured pairs have no pixels differing by more than twelve color levels. This is local check results only.
- All twenty-two Markdown files and 274 relative links/anchors pass validation; twenty distinct selected cases and all thirty-eight pending scope rows remain. `git diff --check` passes.
- The temporary review server is stopped and viewport overrides are reset. Private records and screenshots remain outside Git.

## Remaining work

Keep all twenty cases in [next_batch.md](../next_batch.md), with concrete remaining checks. Finish ABOUT01/HELP01 navigation after this deployment. Finish P07's asset and Terms destination checks and repeat any capture that had not settled before assessing whole completion. Continue P01's links, CV, assets, Overview, and long Research/View All comparisons. Other profiles need remaining links, interactions, and full views despite passing selected content/filter checks.

Search count/order and the missing organization member require source alignment checks; do not force counts, ordering, or membership to match one recorded snapshot. Other information endpoints need separate deployed check results. Every required URL-pattern endpoint must eventually be visually confirmed against Rails.
