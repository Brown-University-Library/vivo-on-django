# Deployed evaluation: second twenty-URL batch

Evaluated October 3, 2026. The owner deployed revision `98cf271`; the loaded revision matches. See the [implementation record](url_batch_002_current_batch.md). Private comparison record label: `url-batch-003-review`. Exact URLs, records, screenshots, and browser observations remain outside Git.

## Each implemented outcome

| Change ID | Deployed result | Check results and limit |
| --- | --- | --- |
| url-batch-002-01 | Verified heading correction. | All fifteen profile Affiliations headings have twenty-one-pixel bottom padding and a fifty-three-pixel height, matching Rails. Populated and empty Affiliations paired views match at 1280×720 and 390×844. View All retains the correction. Existing Publications heading padding/height match where present. Full long-profile completion remains separate. |
| url-batch-002-02 | Verified About/Help availability. | Both pages render their actual content rather than the unavailable response. Bare and slash forms were visited; all observed illustrations load and shared CSS/JavaScript URLs contain content versions. |
| url-batch-002-03 | Partially verified public path behavior. | Header/footer and About/Help cross-links preserve the mounted application prefix. Bare Help stays bare and both slash aliases render. Bare About still ends at its slash form in Brave; the cause is unconfirmed. Keep direct bare About rendering pending instead of inferring whether this comes from a cached redirect or a server rule. |
| url-batch-002-04 | Verified About/Help content and appearance; linked destination remains pending. | Full rendered text/headings and illustration descriptions match Rails at both sizes. Inspected top, lower, and footer pairs differ by at most 0.009% of pixels. The inclusion-policy link stays in the application and retains its fragment; the FAQ destination requires the next deployment. |

## Additional comparison results

All fifteen compared conditional profile-control lists match. All thirty-five publication filter states across ten profiles match the selected button and ordered visible citations through keyboard selection. P01 Affiliations now passes its existing desktop/narrow visual checks, increasing its visual total from four to six of twelve; its functional total remains four of eight.

P07's five profile states were inspected at both widths, including lower content/footer. The organization link reaches its expected destination, direct-entry Back to search opens the default search, and email/Manager destinations match their expected roles without submitting anything. Whole completion remains pending: the Terms footer destination was blocked by the browser, and the supported asset export could not retrieve two observed font files. Eleven image/stylesheet assets were retrieved. An asset-export failure does not establish that the browser failed to render a font. Initial capture differences also need settled comparisons before certifying every visual check.

A portrait that initially appeared unloaded loaded on a later visit. No image code change was justified by that temporary observation. The earlier search count/order and missing-member differences remain open; source alignment has not been established, and this review does not claim a fresh full comparison of those cases.

## Next action

Keep all twenty URLs pending whole completion. Enable the six information pages reached from About/Help and shared navigation, restore their reference content and presentation, and preserve their public URL forms. Check these destinations after deployment, then finish the remaining per-URL checks. Required standalone information endpoints still need their own deployed saved visual checks. The fourteen unavailable historical variations and the previously rejected before-script check remain pending.
