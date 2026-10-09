# First twenty-URL batch: deployed evaluation

Evaluated October 3, 2026, on loaded revision `6088911`. The owner confirmed deployment. Follow [workplan.md](../workplan.md) and the [implementation record](url_batch_001_current_batch.md). Exact pairs and observations remain outside Git under private comparison record label `url-batch-002-review`.

## Each implemented outcome

| Change | Deployed result | Remaining checks |
| --- | --- | --- |
| url-batch-001-01: date separators | Verified selected undated credential and open appointment against Rails. Compared section text on all fifteen profiles; no date text differences remain in that sample. | Whole-page visual and required variations remain separate checks. |
| url-batch-001-02: spacing inside italic book titles | Verified the affected row and all 345 selected citation texts and inline-element sequences. | Full Publications visual comparisons and filter interactions remain pending. |
| url-batch-001-03: closing curly quotes | Verified both affected rows. All 345 selected citation texts and inline-element sequences match. | Other required citation variations and full-page visual checks remain pending. |
| url-batch-001-04: asset content versions | Versioned shared assets appear on eighteen inspected pages. All five fresh sparse-profile bookmarks match Rails, including View All without its button. | About and Help return an unavailable-page response, so their asset use cannot yet be verified. Complete asset/error checks remain pending. |
| url-batch-001-05: search request options | Deployment retains the count/order difference: target 130, reference 131 for the selected search. Local source/request tests establish the options; this does not establish matching source data. | Confirm source index/data alignment, then compare counts, order, facets, highlighting, filters, pagination, and keyboard use. |

## URL and visual coverage

All fifteen profile button lists match, and no broken images were observed on the eighteen rendered pages. Two organization pages were compared; O01 still lacks one reference member, while O03 rendered content matches after excluding the offscreen search label. Source alignment remains unconfirmed.

The owner opened About and Help manually in Brave. Both display the application's unavailable-page response; they are no longer classified solely as browser-blocked checks. The middleware excludes these static handlers in source modes. The next batch enables their existing content and checks presentation locally.

P01 keyboard section selection matches at desktop and narrow widths. Paired screenshots cover all six states and their lower content/footer. Background and Teaching match fully at both widths: four visual checks now pass. Other states remain open: Affiliations heading spacing differs by eleven pixels; Overview has small image differences; long Research content differs in height by about one to two pixels, and View All includes those differences. Preserve these observations rather than treating all captures as passes. Earlier exploratory or interrupted captures are not completion check results.

Whole URLs completed: zero. Twenty URLs carry forward; zero new URLs are added. Every required URL-pattern endpoint still needs its own functional and visual completion check results.
