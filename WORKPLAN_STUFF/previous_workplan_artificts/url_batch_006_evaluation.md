# Deployed evaluation: URL batch 006

Evaluated October 5, 2026 on loaded revision `dedf2c8`. Exact URLs, records, screenshots, and detailed observations remain outside Git under private comparison record label `url-batch-007-review`. Follow [progress.md](../progress.md) and [the next list](../next_batch.md).

Contents:

- [Recorded changes](#recorded-changes)
- [Whole URL results](#whole-url-results)
- [Check results and limits](#check-results-and-limits)
- [Next implementation](#next-implementation)

## Recorded changes

| Previous change | Result after deployment |
| --- | --- |
| url-batch-006-01: bare search and advanced-search URLs | Pass. Generated forms and links retain the application prefix and use bare paths. Both search and advanced slash aliases render. Desktop pointer and narrow keyboard submissions preserve name/title/combined/empty behavior; Back restores fields. Homepage, empty-results and organization search controls reach the expected query. |
| url-batch-006-02: query-preserving Advanced search | Pass for applicable displayed links. Empty-results and an actual filtered, paged search retain the query, repeated filters, and page; Back restores the filtered search. The selected profile variation exposes no Advanced search link. Narrow search hides the link as the reference does. |
| url-batch-006-03: long result titles | Partial. Common long HTML titles match the reference at desktop/narrow widths, while shorter and full profile titles retain their content. Supporting target JSON remains pending: unsigned HTTP redirects to authentication, and ordinary browser JSON navigation is unavailable. Native Console access has not opened. Local HTML/JSON tests pass but do not certify the deployed JSON response. |
| url-batch-006-04: homepage Search button name | Pass. The deployed button has the accessible name Search. Desktop pointer and narrow Enter submissions reach the expected bare search path/query; Back restores the input. |
| url-batch-006-05: book-author URLs | Pass. All observed author hrefs use bare paths with the application prefix. A displayed jacket reaches its corresponding profile. All 98 target images load across 25 groups; the final two-book group and keyboard Previous/Next wrap pass. Book ordering remains a separate open difference. |

Four outcomes pass and one is partial. Do not count the pending JSON portion as passing.

## Whole URL results

Three cases complete this review; the total advances from six to nine. Their four functional criteria are now explicit; this does not imply a numerical increase on an older undefined denominator. Earlier department-submission check results are retained because the fielded-query behavior did not change. Endpoint families and final owner acceptance remain pending.

| Case | Functional criteria F01–F04 | Result |
| --- | --- | --- |
| ADVANCED01, S05 advanced form | F01: matching form/content and bare/slash entry. F02: name, title, combined, department and empty submission behavior with field restoration. F03: Back to search, header/footer navigation and external/configured destinations. F04: required images/assets and relevant browser errors. | 4/4 functional and 2/2 visual. Final settled desktop/narrow form pairs match with zero pixels above the unchanged measured threshold. |
| EMPTY01, S02 no-results variation | F01: matching query and no-results content/controls. F02: query removal/resubmission and Back. F03: query-preserving Advanced search, header/footer navigation and external/configured destinations. F04: images/assets and relevant browser errors. | 4/4 functional and 2/2 visual. Complete desktop/narrow views match, including footer. |
| O04, S08 organization without member groups | F01: matching content and applicable controls. F02: shared search submission and return. F03: content/header/footer links and external destinations. F04: images/assets and relevant browser errors. | 4/4 functional and 2/2 visual. Complete desktop/narrow views match through every footer; no member or visualization control appears in this variation. |

V01 is the complete settled 1280×720 view; V02 is the complete settled 390×844 view. Each includes relevant content below the first screen and the footer. External feedback links retain their own current-page query. Institution links using HTTP on the reference and HTTPS on the target open the same final HTTPS destination. Configured Manager destinations are preserved without entering or submitting that application.

## Check results and limits

Every one of the preceding twenty URLs receives a fresh baseline at both widths: eighty site/width views, forty pairs and 289 captured frames, all reaching the footer. All requested images in these baseline views load. Reference homepage jackets without an image source are deferred by its carousel; the separate target group traversal verifies all 98 target images. Profile baselines cover Overview only. Their other sections, content links, keyboard/bookmark variations and linked CV delivery remain pending; these baselines do not complete those profiles.

All twelve compared profile Overview texts and page heights match. Small raw image differences remain recorded; no tolerance is widened. Organization and no-results views match; O03 still requires member and visualization navigation. Search count/order, one organization member, and homepage book ordering remain different with source alignment unconfirmed. Do not change source queries merely to force these results to match.

Twelve observed target style/script assets return successfully, required images load, and relevant browser warnings/errors are absent for the three completed cases. Settled form records and final advanced-form captures are authoritative. Earlier observations taken before navigation or fonts settled, and keyboard captures whose compositor had the wrong scale, are excluded. Capture JSON determines the valid frame count; stale leftover image files do not add coverage.

The before-script/page-source restriction remains in force. No HTML fetch or authentication-cookie extraction is used. The supporting JSON title check remains pending for a permitted signed-in check.

## Next implementation

[URL batch 007](../current_batch.md) keeps seventeen unfinished URLs and adds Terms of Use, History and Visualization Help. Two demonstrated expanded-filter differences are corrected locally: an empty loading-status paragraph adds unwanted vertical space, and returning from alphabetical to count sorting loses alphabetical ordering among tied counts. Meaningful local browser checks and the full Django suite pass; both corrections require deployment confirmation.
