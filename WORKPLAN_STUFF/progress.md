# Measure progress toward the public-site replacement

Started October 3, 2026. Follow [workplan.md](workplan.md) and [GOAL.md](GOAL.md). This record defines how Codex and the owner measure successive deployed comparisons. It does not certify historical work or owner acceptance. Exact URLs, records, screenshots, and detailed results stay in the outer workspace.

**Estimated URL-case completion: 28.6% — 22 of 77 known cases complete.** This is the provisional case-based estimate requested for an at-a-glance view. It counts completed cases, not implementation effort or final acceptance. The [named inventory](url_completion_inventory.md) shows the denominator, merged aliases and completed cases. Some discovery entries still need reconciliation with the endpoint scope; explain additions or merges when the estimate changes.

Resumption snapshot: October 5, 2026 at 21:19 America/New_York. Seventeen of seventy-seven cases remain complete (22.1%); denominator unchanged. Protected access returns and loaded revision `42eb1e4` is confirmed. The pending citation correction and five affected profiles require current checks. Twenty selected cases and the original October 6 cutoff are unchanged. Next scheduled snapshot is midnight local.

Snapshot: October 5, 2026 at 18:02 America/New_York, first suitable checkpoint after the 18:00 boundary. Completion remains 20/77 (26.0%); the provisional denominator is unchanged. D01 and the repaired portraits retain completed deployed evidence. Latest pushed and loaded revision is `61f0ad1`. TSV corrections pass 302 local tests and all 1,318 saved publication examples against the original serializer; live download and visual checks remain blocked. P11 retains the department membership/title differences under SD02. P12 retains twelve complete individual section states and matching View All interiors, with final boundaries and functional checks still incomplete. Original cutoff remains October 6 at 08:00 America/New_York (12:00 UTC). Next scheduled boundary is midnight local.

Completion checkpoint: October 5, 2026 at 19:00 America/New_York. P12 completes six functional and fourteen complete visual criteria on loaded `33ab1be`, advancing the estimate to 21/77 (27.3%); denominator unchanged. SD04 and affected completed controls pass. D03 remains blocked on a signed-in artifact. Full supporting graph comparisons remain pending. O05 replaces P12 after a clock check; twenty selected cases are twelve carried and eight added. The scheduled 18:02 snapshot above is historical; next scheduled snapshot remains midnight.

Contents:

- [What to measure](#what-to-measure)
- [Current evidence](#current-evidence)
- [Six-hour snapshots](#six-hour-snapshots)
- [Primary profile completion checks](#primary-profile-completion-checks)
- [Run the next iteration](#run-the-next-iteration)

## What to measure

The main measure is completed required URL cases and endpoint patterns. An endpoint passes only when all its required variations have functional and visual evidence, or the owner explicitly accepts a documented difference. Every required URL-pattern endpoint must eventually receive visual confirmation against Rails. A partially checked page is not complete.

Keep separate totals for:

| Measure | Meaning |
| --- | --- |
| Completed URL cases / required cases | Whole cases with all required checks satisfied. |
| Completed endpoint patterns / required patterns | Endpoint patterns whose required cases are complete. |
| Passing deployed functional checks / defined functional checks | Matching content, controls, navigation, response formats, and supporting links. |
| Passing visual checks / defined visual checks | Matching views at the specified size and state, including relevant content below the first screen. |
| Open differences | Known mismatches, identified separately so repeated observations do not inflate the count. |
| Blocked, unavailable, partial, and not-yet-run checks | Checks with insufficient evidence; none count as passing. |
| Changes since the previous deployment | Newly passing checks, resolved differences, and regressions on the same defined checks. |

Use stable IDs for scope rows, URL cases, and individual checks. Scope IDs and discovery case IDs are different fields; some use the same letters and numbers. Before each implementation batch, fix the selected case's passing conditions. Preserve them across deployments. Record newly discovered requirements and changes to the number of checks separately. Do not report one percentage combining local tests, implemented fixes, deployed behavior, and visual coverage.

The thirty-eight scope rows contain grouped endpoints. For the provisional estimate, [url_completion_inventory.md](url_completion_inventory.md) combines sixty-two original discovery specifications with twenty later case names, then merges five known aliases, yielding seventy-seven named cases. The previously completed cases have whole-case evidence in `checklist_completed.md`; all other entries remain pending. The additions include eight publication-profile cases and seven additional information pages after alias reconciliation. This is a useful rough URL-case measure while the remaining interaction and format entries are reconciled with scope, not a precise estimate of engineering time. Do not count screenshots, fragments, commits or individual fixes as additional completed cases.

## Current evidence

Current daily-run evidence includes loaded `88a8548`, evaluated October 5, 2026; preceding evidence remains applicable where recorded. See the [seventh URL-batch evaluation](previous_workplan_artificts/url_batch_007_evaluation.md). Earlier improvement-count evaluations remain historical evidence.

| Observation | Current result | Limit |
| --- | --- | --- |
| Whole URL cases currently complete | 17 (P01, P04, P07, D01, ADVANCED01, EMPTY01, O03, O04, E01, ABOUT01, HELP01, FAQ01, HISTORY01, ROADMAP01, HELP_VIZ01, PUBLICATIONS01, TERMS01) | Partial comparisons do not certify a whole URL. |
| First improvement-count batch | 15 deployed verified; 14 lack qualifying examples; 1 before-script check blocked | Keep these states distinct from local tests. |
| Publication text and inline elements on the original five profiles | Previous full comparison: 278/278 match Rails | Preserved evidence; current selected filter checks also compare visible citation text. |
| Publication filter states | 35/35 match selected control and visible ordered citations | Ten profiles checked with keyboard selection; full visual/link checks remain separate. |
| Expanded twenty-URL citation sample | Previous full comparison: 345/345 texts and inline-element sequences match | Current filter checks pass; full visual/link checks remain pending. |
| Profile content and conditional buttons | All 15 selected profiles match the compared section text and button lists | This does not establish full links, interactions, assets, or visual coverage. |
| Sparse-profile fresh bookmarks | 5/5 match Rails | P07 passes all five functional and ten visual criteria after settled capture and asset checks. |
| Shared asset content versions | Present on profiles and About/Help | All observed information-page illustrations load. P07 asset evidence passes; font delivery and byte comparisons explain the export-tool limitation. Other case audits remain pending. |
| Primary profile completion checks | 8/8 functional passed; 12/12 visual passed | Complete CV bytes, all eleven pages, signed-in delivery behavior, Overview navigation and complete section views pass. Other profile variations remain pending. |
| Search and organization content | Previously observed count/order and missing-member differences remain open | Fresh complete desktop/narrow baselines inspected; source alignment is unconfirmed. |
| Information pages | All eight retain complete checks and pass the added SD05 title requirement | Both observed About aliases and every FAQ anchor are confirmed. The separate institution page remains pending. |
| Search/homepage deployment outcomes | 5/5 complete; long-title HTML and signed-in JSON pass | Permitted read-only Console checks confirm keyword and browse titles. |
| Cases completed during the preceding review | ADVANCED01, EMPTY01 and O04 each pass 4/4 functional and 2/2 visual checks | These criteria are now explicit; they do not imply an increase on an earlier undefined denominator. |
| Fresh preceding-batch baseline | 20 URLs, 40 desktop/narrow pairs, 289 frames through all footers | Profile coverage is Overview only; other states remain pending. |
| P03 completion evidence | 6/6 functional criteria pass; 12/12 complete visual views pass | Filtered/paged return, CV bytes, all five rendered pages and signed-in delivery pass; the selected whole case completes. |
| Expanded-filter deployment outcomes | 2/2 corrected outcomes pass | All applicable named dialogs match tie ordering and 15-pixel settled first-row spacing at both widths. Search source-data differences remain open. |
| P08/P09 daily-run evidence | Each completes 6/6 functional criteria; P08 14/14 and P09 10/10 complete visual states | Shared document correction passes on `9140ef0`; current applicability observations retain unchanged complete profile evidence and inspected PDF pages. |
| Current URL-based batch | 20 distinct URLs: 11 carried forward, 9 added | E01, P10, P08 and P09 complete during the daily run. D01/D02 fill the two latest completed slots after clock checks. Other whole cases and existing blockers remain pending. |

Measure the same checks before and after deployment. Use content versions on changed assets to avoid reusing older browser resources; verify actual served bytes and rendered behavior rather than assuming the requested version proves delivery. Confirm collected copies during deployment, then refresh without cached resources when the browser still uses older bytes. Source count/order differences stay open until explained and checked.

Brave browser access was confirmed by reading the owner's signed-in staging homepage. Use its documented browser controls for ordinary page, interaction, and visual checks. Browser access does not supply absent source variations. The earlier page-source viewing rejection remains in force; do not use another browser to obtain that blocked result. The before-script condition remains pending until a permitted check is available.

P10 passes all five functional and fourteen complete visual conditions on `5dd7b1b`. Its section content, publication filters, controls, bookmarks, return navigation, destinations and assets agree. Full graph cases remain separate; two identical external publisher errors limit publisher availability rather than the compared destination behavior.

## Six-hour snapshots

During active improvement work, use `America/New_York` boundaries at 00:00, 06:00, 12:00 and 18:00. Update at the first suitable checkpoint after a boundary; do not interrupt a browser interaction just to hit an exact minute. Also update at daily start, resumption and final handoff. If several boundaries pass during an interruption, write one honest current snapshot when work resumes rather than invent historical results. No separate scheduled task runs while the chat is idle.

1. Read the completed checklist and pending/regression records. Update the named inventory's whole-case states; retained passes need their existing evidence, and reopen a case when a regression invalidates completion.
2. Count completed canonical case IDs once, divide by the total named inventory, and show the fraction and percentage at the top of this file. Keep local-only, blocked, partial and unverified cases in the denominator. Preserve the alias map; record any additions, merges or exclusions and their reasons. Do not reduce the denominator merely because evidence is difficult to obtain.
3. Record the snapshot time, latest verified revision, latest pending release, resolved differences, regressions, blocked checks and exact next action. Keep detailed results private. If nothing passed since the preceding snapshot, retain the same percentage and say so. An unchanged snapshot is still useful confirmation.
4. Add a concise history row below. Update the last-snapshot time and next six-hour boundary in `../../ongoing_run.local.md`. Group safe tracking commits with normal release/pass records when authorized; do not trigger a deployment solely to satisfy every clock boundary.

| Snapshot | Completed / known cases | Estimated completion | Verified evidence / remaining limit |
| --- | --- | --- | --- |
| October 5, 2026 — workflow update | 15 / 77 | 19.5% | Existing whole-case evidence through `88fb8e4`; `f40c0dd` requires verification. Inventory v1 is provisional; no new deployed checks run during this update. |
| October 5, 2026 at 12:43 America/New_York — daily start | 15 / 77 | 19.5% | Denominator unchanged. Loaded `aae7a67` includes pending changes; per-change checks begin. No new whole case passes at start. |
| October 5, 2026 at 14:10 America/New_York — verification checkpoint | 16 / 77 | 20.8% | E01 completes on `95a4f65`; denominator unchanged. P08 retains the document error-response review. Next scheduled boundary remains 18:00 local. |
| October 5, 2026 — 14:54 verification checkpoint | 17 / 77 | 22.1% | P10 completes on loaded `5dd7b1b`; O02 replaces its slot. No denominator change; P08/P09 document response difference remains. |
| October 5, 2026 at 15:48 America/New_York — resumption | 17 / 77 | 22.1% | Loaded `fd6d0a8c` confirmed. No new whole case or denominator change. Retain P11 visual evidence; unfinished functional checks and SD01 remain pending. |
| October 5, 2026 at 16:17 America/New_York — document verification | 19 / 77 | 24.7% | Denominator unchanged. P08/P09 complete on loaded `9140ef0`; SD01 resolves and completed CV regressions pass. P11 remaining navigation/asset checks stay pending. |
| October 5, 2026 at 17:44 America/New_York — document and portrait verification | 20 / 77 | 26.0% | D01 completes on loaded `7ae8ab1`; department loading and larger portraits pass. Missing-member/title differences remain. Denominator unchanged. |
| October 5, 2026 at 18:02 America/New_York — 18:00 boundary checkpoint | 20 / 77 | 26.0% | Count and denominator unchanged. Loaded `61f0ad1`; TSV live comparison remains blocked despite complete local serializer checks. Native browser captures remain unavailable. |

The estimate can decrease when scope gains required cases or a regression reopens a case. Explain that change instead of hiding it. A later estimate of work remaining may be added separately with its basis and uncertainty; it must not replace or silently change this measured fraction. Complete endpoint coverage, integration checks and owner acceptance remain separate requirements even if all currently named cases pass.

## Primary profile completion checks

P01 is complete under these original twenty checks. Preserve their definitions and historical evidence; publication variations belong to separate cases. Record newly demonstrated requirements separately. Each visual check includes the selected section, controls, heading, full relevant content, and footer. Match browser, viewport, loading state and scroll position between Rails and Django. Preserve paired evidence and record any missing capture.

| Check ID | Passing condition | Current evidence |
| --- | --- | --- |
| P01-F01 | Every section and View All show the expected panels and matching rendered content. | Passed after deployment. |
| P01-F02 | A profile opened from the referring filtered search returns to that exact search, preserving repeated filters and its page. | Passed after deployment for the tested primary-profile journey. |
| P01-F03 | Direct entry after an unrelated search returns to default search. | Passed after deployment. |
| P01-F04 | Keyboard use selects each available section and exposes the expected active state. | Passed on P01 at desktop/narrow widths; each available section and View All exposes the expected panels and selected control. |
| P01-F05 | Internal content links, including institutions, organizations, and research areas, reach the expected destinations and retain required queries. | Passed on `a3bca98`: all seven internal content links reach their expected paths and queries. |
| P01-F06 | External content links and the Manager link retain their required destinations; email links expose the expected address without sending mail. | Passed on `a3bca98`: external/email hrefs match and the Manager retains its configured destination. |
| P01-F07 | The linked CV opens the expected document and its required delivery checks pass. | Passed on `11fa230`: complete matching bytes, all eleven rendered pages, and signed-in delivery checks. |
| P01-F08 | Required images, fonts, styles, and scripts load; relevant browser errors or failed resources are explained. | Passed on `ee0c95f` and retained on `11fa230`: complete browser image loading, required asset delivery and matching bundled font bytes, with no relevant warnings/errors. Protected-image metadata redirects alone are not failures or delivery proof. |
| P01-V01 | Desktop Overview matches at 1280×720, including relevant content below the first screen. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V02 | Desktop Research matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V03 | Desktop Background matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V04 | Desktop Affiliations matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V05 | Desktop Teaching matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V06 | Desktop View All matches at 1280×720. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V07 | Narrow Overview matches at 390×844, including relevant content below the first screen. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V08 | Narrow Research matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V09 | Narrow Background matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V10 | Narrow Affiliations matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V11 | Narrow Teaching matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |
| P01-V12 | Narrow View All matches at 390×844. | Passed on `ee0c95f` and retained on `11fa230`: complete paired content and footer captures match layout. Raw image/pointer differences remain recorded; no tolerance is widened. |

Starting results under this explicitly defined checklist: functional checks 3/8 passed; visual checks 0/12 complete, with two partial views; whole case pending. These stricter whole-case criteria do not erase the observed Overview matches or change the fifteen verified batch improvements. They expose what remains before calling the URL complete.

P04 preserves five original functional and ten visual conditions, plus the separately added institution requirement. On `11fa230`, all five original functional, all ten visual, and the added requirement pass. The configured Manager value is echoed consistently on homepage/profile; local environment differences are not deployed failure evidence. The whole selected case completes. About/Help/FAQ each pass four defined functional and two complete visual checks. These newly explicit information-page denominators do not imply an increase on an older undefined count.

## Run the next iteration

1. Codex records the twenty selected URLs, their fixed passing conditions, current evidence, and specific remaining work in [next_batch.md](next_batch.md). Preserve stable case IDs and private URL bindings. Reconcile endpoint coverage while continuing useful work on selected URLs.
2. Codex reviews each URL and makes as many relevant improvements as reasonably possible, preferring to finish an individual URL. Record per-change expected outcomes in [current_batch.md](current_batch.md). Missing source variations remain pending without repeated searches for examples.
3. Codex runs required local checks and releases reasonable groups when the owner's current prompt authorizes commits/pushes. The scheduled caller deploys; Codex follows [automatic deployment checks](workplan.md#automatic-deployment-and-verification), including loaded revision and actual asset delivery. Continue without waiting for owner confirmation; do not push another release until the preceding release's verification is accounted for.
4. Codex verifies every recorded change and affected previously passing behavior after each release. At the pass boundary, account for all selected URLs and required checks as passed, different, blocked, unavailable, partial or not run. Retain applicable earlier evidence for unchanged checks with its revision and reason. Compare desktop/narrow views and relevant lower content under matching conditions. Keep source-data differences separate.
5. Codex reports prior/current totals, resolved differences and regressions. Complete only whole verified URLs, update [the inventory](url_completion_inventory.md), and carry unfinished URLs with concrete actions. Refill and begin another pass only before the fixed daily cutoff. At the cutoff, finish the active pass and handoff. Refresh the completion snapshot using the procedure above.

For repeatable supported comparisons, reuse the existing [comparison command and guide](../docs/conversion/browser_comparison.md), which produce structured observations, paired screenshots, and pixel-difference reports. The existing command has limits and does not establish signed-in deployed access on its own. Use documented browser controls where needed. Do not bypass a rejected browser action or copy authentication cookies into helpers.

Current results on the same P01 checklist: functional checks 8/8 passed; visual checks 12/12 passed; whole case complete. Four preceding search/homepage outcomes pass on `dedf2c8`; the fifth now also passes supporting JSON on `88fb8e4`. Both expanded-filter corrections pass after collection and browser refresh. The institution fallback and missing-record wrapper corrections in [current_batch.md](current_batch.md) pass deployed checks; illustration delivery and the remote collected-file command remain pending.

The settled capture method limits native wheel movement to the remaining page height. Excess movement produces elastic overscroll and misleading white bands. Observe completed image loading and record whether long captures actually reach the footer; a fixed frame limit is not full-page evidence.

October 5, 2026 at 13:19 America/New_York: E01 completes four functional and two complete visual criteria on loaded `95a4f65`, confirmed again after comparison. Whole cases advance to 16/77 (20.8%); denominator unchanged. Institution fallback placement also passes, but illustration delivery remains unavailable. The remote collected-file command is not run; served bytes pass. Next scheduled snapshot remains 18:00 local time.

Title-check checkpoint: SD05 adds a demonstrated browser-title requirement for the nine information/institution pages. Eight previously completed information cases are temporarily pending; their full-page evidence is retained. The provisional denominator stays seventy-seven; current completion is thirteen (16.9%) until the new deployed title checks pass. This change to required checks is separate from the earlier profile completion.

October 5, 2026 at 19:22 America/New_York: release `88a8548` is loaded and fully accounted for. SD05 restores eight information cases after the added title requirement passes; O03 completes four functional and two complete visual criteria. Current completion is 22/77 (28.6%); denominator unchanged. O06 replaces O03 after a clock check. The next scheduled snapshot remains midnight; original October 6 cutoff is unchanged.


SD06 adds the demonstrated search-history requirement F02a. After an actual search/profile/Back journey, Forward must restore the profile, matching the reference. P01, P03, P04, P07, P08, P09, P10 and P12 temporarily reopen for this new shared check; their complete content, controls, document and visual evidence is retained. Whole completion is fourteen of seventy-seven (18.2%); the provisional denominator and rolling twenty membership are unchanged. Direct and unrelated-referrer entries must still open the default search.


SD06 is verified on loaded `6ede886`. Thirty-six actual search/default/Back/Forward journeys and four repeated-filter/Page1 journeys pass at both widths. All nine rendered section-content sets match; required settled images and fonts load. Eighteen current paired viewport views are manually inspected; premature portrait captures are excluded and replaced. Earlier complete page, document and navigation evidence remains applicable because only the search-return action changed. P01, P03, P04, P07, P08, P09, P10 and P12 regain Complete. Whole completion returns to twenty-two of seventy-seven (28.6%); denominator and membership are unchanged. P13 retains its separate blocked department and incomplete CV checks; current served bytes and resources pass.


SD07 reproduces the reference publication-link wrapper even when a citation has no outgoing links. The missing empty wrapper causes a narrow citation to be one line shorter. A private local browser comparison reproduces the old and corrected heights; all 302 tests, changed-file Ruff and project Pyright checks pass. Deployed citation content, links, filters and complete Publications/All views remain pending. P03, P08, P09, P10 and P12 temporarily reopen for these affected checks; their unrelated complete evidence remains applicable. Whole completion is seventeen of seventy-seven (22.1%); denominator and rolling membership are unchanged. Fresh target review requires renewed sign-in. No deployed pass is claimed from an already loaded document.


Access checkpoint: October 05, 2026 at 20:55 America/New_York. Release `42eb1e4` is confirmed loaded. SD07 has passing local layout, tests, lint and type checks; its required deployed rendering checks are pending. Whole cases remain 17/77 (22.1%); five profiles await affected citation checks and the denominator is unchanged. P14 retains its earlier ten matching full views, with two narrow differences; new-release applicability remains pending. The original October 6, 08:00 cutoff and rolling twenty membership remain fixed.


SD07 is verified after deployment on `42eb1e4`. Current citation text, inline formatting, row geometry and all offered ordered filters agree at both widths. Four affected complete P14 views and every changed citation region are visually inspected. The five reopened profiles also pass their affected boundaries and required resource checks; unchanged complete interiors, navigation and document evidence remain applicable. P03, P08, P09, P10 and P12 regain Complete. Whole completion returns to twenty-two of seventy-seven (28.6%); denominator and rolling membership are unchanged. P14 now passes all twelve visual criteria and its complete content/filter check, while remaining target interactions, links, document delivery and resources are pending. Private evidence label `daily-run-2026-10-05`.


October 5, 2026 21:57 checkpoint: completion remains 22/77 (28.6%), with no denominator or membership change. All release 15 changes are accounted for. P14 adds passing section controls, resource delivery, full CV pages and response comparisons, but retains a browser-blocked destination, incomplete desktop viewer captures and the first-page URL correction awaiting deployment. Release 16 local checks pass; no new deployed or whole-case completion is claimed. Next scheduled snapshot remains midnight local.
