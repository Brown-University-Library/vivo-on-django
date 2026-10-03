# Batch 002 deployed evaluation

October 3, 2026. The owner confirmed deployment. Loaded revision `2ba9b1f`; application commit `75269fc`. Private evidence label: `batch-002-profile-checks`. Exact bindings and detailed evidence remain outside Git. This evaluation records every implemented outcome; it does not certify whole URLs or owner acceptance.

## Per-improvement results

| Improvement | Deployed outcome | Remaining check and next action |
| --- | --- | --- |
| batch-002-01 | Citation text and inline elements pass: all 278 selected citations across P08–P12 match Rails, including all five previously different P10 collection titles. | Complete desktop/narrow Publications views and remaining links before certifying whole URLs. |
| batch-002-02 | Partial pass: required empty panels exist on P04/P07 and conditional buttons match. P04 View All displays the empty Affiliations heading as Rails does. | Complete matched desktop/narrow views; recheck P07 View All after the script refresh below. |
| batch-002-03 | Difference remains: fresh P04 Affiliations and P07 Background/Affiliations/Teaching/All bookmarks still show Overview in the reviewed browser. The server supplies the updated script, whose contents match the committed script. | Add content versions to script URLs, deploy, then repeat fresh-bookmark and ordinary-control checks. Old browser caching is a possible cause; it is not established by the server asset check alone. |

## Follow-up

The evaluation pass is recorded, but two improvements still have unfinished checks. Whole URL cases remain pending. Carry them into [the first 20-URL batch](../next_batch.md). Keep the first batch's fourteen unavailable real-source variations and blocked before-script check pending; do not count local tests as deployed passes or retry the rejected page-source result indirectly.

Additional review finds open date-range separators, book-title spacing, and closing curly quotation differences on selected profiles. Organization member content and search count/order also differ; underlying source alignment requires investigation. These observations do not change the settled endpoint scope. Every required URL-pattern endpoint must eventually be confirmed visually against Rails.
