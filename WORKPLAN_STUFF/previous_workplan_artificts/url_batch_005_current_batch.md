# Current batch: twenty URLs

Batch: url-batch-005, October 5, 2026. Follow [workplan.md](../workplan.md), [next_batch.md](url_batch_005_next_batch.md), and [../AGENTS.md](../../AGENTS.md). Twenty URLs carry forward; none are added. Exact pairs remain in `../../../url_batch_005/urls.json` and `../../../current_urls.local.md`, outside Git. The preceding [implementation](url_batch_004_current_batch.md), [selected list](url_batch_004_next_batch.md), and [deployed evaluation](url_batch_004_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `ee0c95f`; the loaded revision matches. Both preceding improvements pass their specified deployed checks at desktop and narrow widths. P01 passes seven of eight functional and twelve of twelve visual checks, including the complete long Research and View All content through the footer. P04 passes ten complete visual checks and matching settled bookmark panels. Its Overview fragment differs from the reference. P07's previously completed views remain matched. Twelve other selected profiles pass the fresh Overview link-style subset; their whole-case checks remain pending.

Application commits `fafaff3` support partial PDF requests and `a51fcfa` match Overview URL behavior. Both changes are checked locally and await deployment; they do not increase deployed pass totals. The tracking commit follows them. The final handoff and private checkpoint record its ID and the confirmed push.

## Changes and deployed checks

| Change ID | Cases and change | Local check results | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-005-01 | P01 linked CV and required PDF endpoints: support a single requested byte range, accurate lengths, and body-free HEAD responses. Complete downloads retain every byte. | Reference binary delivery supports a single byte range; the existing handler returns the whole document. Focused helper and endpoint tests cover closed/open/suffix ranges, unsatisfied requests, full downloads, HEAD, invalid/multiple fields, and unconfirmed If-Range. | Confirm a signed-in CV opens and displays every page; compare the downloaded document and delivery metadata. Verify a single range returns the requested bytes with 206 and Content-Range; full GET/HEAD remain correct. Do not count an unauthenticated sign-in redirect as document-handler check results. |
| url-batch-005-02 | P04 and affected profiles: returning to Overview or opening its explicit bookmark removes the section name from the fragment, matching the reference. | Fresh keyboard and bookmark comparisons expose the difference; reference implementation confirms the expected fragment. The correction retains the selected control and existing section behavior. JavaScript syntax checking passes. | Check keyboard and pointer navigation back to Overview and fresh Overview bookmarks at both widths. Confirm active controls, visible panels, other fragments, and profile content remain correct; recheck P01 and completed P07. |

## Local validation

- Full Django suite: 281 tests pass, including the new document delivery tests.
- Ruff lint and formatting: all four changed Python files pass.
- Pyright: all four changed Python files pass with zero errors/warnings using the project interpreter, Python 3.12, and basic checking. Pylance is unavailable.
- JavaScript: `node --check vivo_app/static/js/tabs.js` passes.
- All twenty-four workplan Markdown files and 256 relative links/anchors pass validation. Twenty distinct selected cases and all thirty-eight pending scope rows remain. `git diff --check` passes. Private check records stays outside Git.

## Remaining work

After deployment, confirm both changes and affected previously passing behavior. P01's full CV comparison is incomplete: a viewer opening alone does not prove the downloaded document or delivery behavior. P04 retains its configuration/external-link checks and the Overview fragment difference until deployed confirmation. Its two institution links now reach the expected decoded queries; that newly enumerated requirement is recorded separately from its original five functional checks.

All twenty URLs remain selected. Finish the other profiles' full links, interactions, assets and views, and the information pages' remaining navigation/assets. Organization membership and search count/order differences remain open because source alignment is unconfirmed. Fresh profile-footer About navigation no longer reproduces the earlier slash observation; do not infer a cause or erase missing direct-entry coverage. The earlier before-script source restriction remains in force. Every required endpoint eventually needs visual confirmation.
