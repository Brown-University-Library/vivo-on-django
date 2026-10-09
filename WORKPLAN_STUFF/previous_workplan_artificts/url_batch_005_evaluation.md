# Deployed evaluation: URL batch 005

Evaluated October 5, 2026 on loaded revision `11fa230`. Exact URLs, PDFs, screenshots, metadata, and detailed observations remain outside Git under private comparison record label `url-batch-006-review`. Follow [progress.md](../progress.md) and [the next list](../next_batch.md).

Contents:

- [Recorded changes](#recorded-changes)
- [Whole URL results](#whole-url-results)
- [Check results and limits](#check-results-and-limits)
- [Next implementation](#next-implementation)

## Recorded changes

| Previous change | Result after deployment |
| --- | --- |
| url-batch-005-01: PDF range delivery | Pass. The downloaded CV matches every reference byte; all eleven rendered pages are visually inspected. Signed-in browser requests confirm the requested 32 bytes with 206, accurate Content-Range and length, complete HEAD metadata, and an unsatisfied-range response with 416 and an empty body. |
| url-batch-005-02: Overview fragments | Pass. Thirty-six fresh-bookmark, keyboard, and pointer observations across P01, P04, and completed P07 match at actual desktop and narrow dimensions. Other P04 sections retain their matching hashes, active controls, panels, and content. |

## Whole URL results

Five cases complete this review; the total advances from one to six. Endpoint families and final owner acceptance remain pending.

| Case | Defined checks | Result and check results |
| --- | --- | --- |
| P01, S07 rich profile | Original eight functional and twelve visual checks | 8/8 functional, 12/12 visual. Final CV check F07 passes; fresh complete section captures retain matching content and layout. Earlier unchanged navigation checks remain supporting check results. |
| P04, S07 profile without research | Original five functional and ten visual checks; one separately added institution requirement | 5/5 original functional, 1/1 added functional, 10/10 visual. Keyboard/bookmark behavior matches. The Manager href is the configured value echoed consistently on homepage and profile; local environment values do not substitute for the deployed setting. External destinations and footer navigation pass. |
| ABOUT01, S24 About | Four functional and two visual checks, fixed before the remaining review | 4/4 functional, 2/2 visual. Content, internal and external destinations, keyboard navigation, and supporting assets pass. Both observed bare and slash direct-entry routes render the expected content. |
| HELP01, S24 Help | Four functional and two visual checks, fixed before the remaining review | 4/4 functional, 2/2 visual. Internal destinations, linked illustrations, external/configured links, and supporting assets pass. |
| FAQ01, S24 FAQ | Four functional and two visual checks; existing anchor requirements retained | 4/4 functional, 2/2 visual. All twelve links activate the expected named anchors and scroll destinations with the keyboard; previous pointer checks remain supporting check results. External/email links and shared navigation/assets pass. |
| P07, completed sparse profile | Previous five functional and ten visual checks | Remains complete. The changed Overview behavior and all ten complete views show no application regression. |

The About/Help functional check totals are now explicit; do not present them as a numerical increase on an older undefined denominator. The original P01 denominator remains eight and P04 remains five, with its added requirement kept separate.

## Check results and limits

The affected profile and information comparisons contain thirty-eight state/width pairs and 146 paired frames, all reaching their footers. The compared text matches after removing only the documented offscreen search label and malformed reference email-label prefix. All six complete information views have zero pixels above the unchanged difference threshold. Profile captures retain raw differences, including browser pointer indicators; fresh state/footer inspection and the earlier complete visual review establish no application layout regression. Two public font binaries match the bundled files, observed scripts/styles return successfully, and relevant page warnings/errors are absent.

Earlier wrong-viewport observations are archived and excluded. The browser's font/sheet enumeration and unsettled carousel observations are not authoritative check results. No before-script HTML retrieval is repeated and no authentication cookies are extracted.

Other selected profiles retain their remaining full links, interactions, and views. Source count/order and organization membership differences remain open. Partial results do not complete a URL or endpoint family.

## Next implementation

[URL batch 006](../current_batch.md) selects fifteen unfinished URLs and adds five: homepage, advanced search, no-results search, default browse search, and a sparse organization. Matching complete views are observed for advanced search, no-results search, and the added organization. New search-link, title-length, homepage button-name, and author-link changes require deployment confirmation. Default-search count/order and homepage book order remain different; the corresponding source queries match the Rails implementation, so these differences do not justify changing the queries without further check results.
