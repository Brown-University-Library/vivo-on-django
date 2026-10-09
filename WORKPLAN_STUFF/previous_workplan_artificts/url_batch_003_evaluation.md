# URL batch 003 deployed evaluation

Evaluated October 3, 2026. Loaded revision `a3bca98` matches the pushed application commits. Exact URLs, raw observations, metadata, screenshots, and resumption notes stay outside Git under comparison record label `url-batch-004-review`. See the [implementation](url_batch_003_current_batch.md) and [selected URLs](url_batch_003_next_batch.md).

## Each recorded change

| Change | Deployed result | Check results and limit |
| --- | --- | --- |
| url-batch-003-01 | Pass for the six supporting information destinations. | Full FAQ, History, Roadmap, publication help, Terms, and visualization-help pages render with expected illustrations and shared presentation. Live deployment is checked; prepared/replay behavior remains covered by local tests. |
| url-batch-003-02 | Pass for all six bare routes, retained slash aliases, and the Roadmap link. | All six bare routes render. All six slash aliases render. Help navigation reaches every destination; Roadmap preserves the mounted visualization-help path. About still reaches its slash form and remains a separate unresolved observation. |
| url-batch-003-03 | Pass for restored full content and presentation. | All six full rendered texts match. Forty supporting-page screenshot pairs at desktop/narrow widths have zero pixels differing by more than twelve color levels and were visually inspected. All observed images load. Twelve FAQ and six publication-help anchor links have targets; every FAQ link and a final publication-help link activate the correct fragment and scroll destination. |

About and Help also match full rendered text and eight paired screenshot frames at both widths. Actual Help navigation reaches all six expected destinations. These comparisons do not certify their remaining external/shared navigation and asset checks.

## Completed case and measured progress

P07 satisfies its previously defined five functional and ten visual checks. The source/target full text matches after excluding offscreen accessibility labels; all five states match at both widths, including footer. All twenty final screenshot pairs have zero pixels differing by more than twelve color levels. Two initial Overview captures had tiny differences inside an image; repeating the pair at the verified 1280×720 viewport removes them. Internal organization navigation, direct-entry default-search return, and email/Manager destination checks retain prior passing check results. The repaired Terms footer destination now works. Observed images load, styles/scripts have successful delivery metadata, both observed fonts return valid bytes matching the bundled files, and browser warnings/errors are absent.

An unauthenticated image metadata request redirects to sign-in; the signed-in browser displays the image correctly. The missing font response type prevents the asset export tool from saving those files, but does not establish failed font delivery. No authentication data was copied into a helper.

P01's seven internal content links reach their expected paths and queries. External/email destinations match, with the Manager using its configured destination. Its fixed functional total increases from 4/8 to 6/8. Its visual total stays 6/12: new captures demonstrate Research link styling and research-area spacing differences; some narrow captures reached the twelve-frame limit or had a portrait still loading. The CV link opens an eleven-page PDF and its first page was inspected, but complete document/delivery comparison remains pending.

Whole completed cases increase from zero to one. Completed endpoint families remain zero; P07 does not complete S07 or establish final owner acceptance. Search count/order and organization membership differences remain open without source-alignment check results.

## Next actions

Keep nineteen unfinished cases, add FAQ01, and work from the [next twenty URLs](../next_batch.md). Correct the demonstrated profile styles and spacing, then repeat affected views and links after deployment. Every required endpoint and variation still needs its own saved visual checks. Keep the earlier blocked before-script condition pending.
