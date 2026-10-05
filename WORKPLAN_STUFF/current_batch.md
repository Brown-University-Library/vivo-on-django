# Current batch: twenty URLs

Batch: url-batch-008, October 5, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). The initial list contains seventeen carried URLs and three added URLs. After three more whole cases finish, the refilled next list contains sixteen carried URLs and four added URLs. Exact pairs and evidence stay in `../../url_batch_008/` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_007_current_batch.md), [selected list](previous_workplan_artificts/url_batch_007_next_batch.md), and [evaluation](previous_workplan_artificts/url_batch_007_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Pass and release record](#pass-and-release-record)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `88fb8e4`. Both preceding expanded-filter corrections pass after static collection and a browser refresh without cached resources. Terms of Use, History and Visualization Help complete four functional and two visual checks each; whole cases advance from nine to twelve. P03, Roadmap and Publications Help subsequently complete their defined checks, bringing the total to fifteen. Endpoint families and owner acceptance remain pending.

Daily-run verification on October 5, 2026 confirms `response.loaded_version` at `aae7a67`, including application commits `fb860ad` and `2d2fad0` and their tracking records. All eight institution-page stylesheets and the search script match local source bytes. The remote collected-file command is not run because no server command access is established. Both institution routes render; text, four internal keyboard destinations and search/return pass. Paired desktop/narrow views expose different fallback text for the unavailable illustration; the focused correction passes on loaded revision `38beb8d`. The missing-record correction moves the search area into its existing error wrapper, removing an extra empty block. E01 subsequently completes on loaded `95a4f65`, bringing whole cases to sixteen. The fixed daily cutoff is October 6, 2026 at 08:00 America/New_York (12:00 UTC).

Follow [the automatic procedure](workplan.md#automatic-deployment-and-verification) for pending checks. The next invocation confirms the expected loaded revision and actual asset delivery itself; it does not wait for another owner deployment message. The historical verified results above retain their original revision.

## Pass and release record

The daily run starts October 5, 2026 at 12:43 America/New_York. Its sole writer, finite active-pass actions and fixed October 6 cutoff are recorded in `../../ongoing_run.local.md`. [next_batch.md](next_batch.md) preserves the prepared twenty-case list. Resuming a recorded daily run keeps that run's cutoff.

| Release | Change IDs | Implementation / tracking commits | Expected remote revision and push | Observed loaded revision / verification | State and next action |
| --- | --- | --- | --- | --- | --- |
| url-batch-008 release 1 | 008-01 through 008-03 | `fb860ad`, `2d2fad0`; tracking `f40c0dd` | Full revision and confirmed October 5, 2026 11:38 EDT push in private checkpoint | Loaded `aae7a67`; source-mode rendering, routes, served assets and navigation pass; fallback subsequently corrected | Accounted for: served bytes pass; remote collected-file command not run and illustration unavailable. |

For subsequent releases, record the full expected and confirmed remote commits, push time, actual loaded commit, verification time, per-change result and next action privately; keep safe summaries here. Record pass start time and finite planned actions before starting it. Verify changed behavior and affected passing cases for each release, then account for all selected cases at the pass boundary. Check [progress.md](progress.md#six-hour-snapshots) for a due snapshot. After the cutoff, finish existing actions and records without refilling or starting another pass.

## Changes and deployed checks

| Change ID | Change and reason | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-008-01 | Add a deployment-only check for missing, unreadable or stale collected application CSS/JavaScript. Earlier rendered pages request current version queries while the web server still supplies previous copies. Document static collection after every update. | Five focused checks cover matching copies, missing/stale copies, configured source overrides, missing configuration/sources and deployment-only registration. The check reads files without requesting services or changing data. | Run static collection and `check --deploy --tag staticfiles` from the application checkout. It must pass with current copies. Confirm the actual served bytes and affected filters separately; directory mapping and browser caches remain separate checks. |
| url-batch-008-02 | Clarify complete interactive screenshot coverage and settled dialog observations. Verify the selected tab, actual bitmap size, scroll position zero and footer coverage. | Corrected paired captures and exact named-dialog records replace observations made at the wrong scale, scroll position or animation state. | Apply these checks during every affected browser comparison. Incorrect captures must not increase visual pass totals. |
| url-batch-008-03 | Render the additional institution information page in source modes, preserve no-slash/slash entry, use the shared public styles and keep existing profile/individual links local with any mount prefix. Match the reference punctuation. | Route/template tests cover both forms in prototype/prepared/replay/live modes and prefixed links. Local browser rendering confirms the heading, public styles and local destinations. | Confirm direct/slash entry, full content, four internal destinations, search/return and full desktop/narrow views. Reconcile the illustration that fails on the reference and local pages. |
| url-batch-008-04 | Match the institution illustration fallback text to the reference. The unavailable image exposes a different label and horizontal position in both layouts. | Direct paired views demonstrate the difference; only the template alternative text changes. Full suite: 289 tests pass. No Python file changes. | Confirm the fallback label and its placement at both widths, retain the failed image observation, and recheck the four content destinations and search/return. |
| url-batch-008-05 | Keep the missing-record search area inside its error wrapper, matching the reference layout. The separate wrapper leaves a large empty region before the search. | Reference and target rendered structure and positions demonstrate the difference. An offline browser preview moves the search to the reference vertical position without changing recovery links or form controls. All 289 tests pass; no Python changes. | Confirm 404 behavior, recovery links, keyboard search/return, required assets and complete desktop/narrow views. Preserve changing background images and any remaining width/capture differences as separate observations. |

## Local validation

- Full Django suite: 289 tests pass, including five new deployment checks.
- Ruff lint and formatting pass for all eight changed Python files.
- Pyright uses the project interpreter, Python 3.12 and basic checking: zero errors or warnings in all eight changed files.
- The management command detects 22 stale/missing local copies and gives the documented collection hint; the matching-copy test passes. No local collection is needed for this validation.
- Tracking files, relative links, selected counts and `git diff --check` are checked before pushing.
- Required images load in the signed-in browser; current public page styles, scripts and fonts have supporting delivery evidence. Unused CSS references and unauthenticated portrait redirects remain distinct from required browser resources.

## Remaining work

P03 completes all six functional criteria and twelve full section views. Actual return after selecting two filters and paging preserves the originating search. Its CV bytes, all five pages and signed-in HEAD/range responses pass. The owner enables Console pasting manually; permitted read-only PDF and supporting search JSON checks then run successfully. Long JSON titles pass on keyword and browse search. Roadmap and Publications Help each pass four functional and two visual criteria, including all six Publications anchors.

Search count/order, organization membership and homepage book ordering remain different; source alignment is unconfirmed. Other carried profiles retain explicit pending sections, links, interactions and documents. The institution page now opens in native Brave at both route forms. Deployed text and navigation pass; the initial complete paired views identify the illustration fallback difference, corrected in release 01. The illustration fails on both sites, so its delivery remains unavailable and the whole case stays pending. The earlier browser block is historical. The fallback correction passes full desktop/narrow paired views on `38beb8d`; raw pointer differences remain separate. The remote collection command and illustration delivery retain their pending states. The three replacements require the complete criteria in [next_batch.md](next_batch.md). Every required endpoint eventually needs visual confirmation. The separate Manager and the deferred Research Areas download correction remain outside this batch. The before-script/source restriction remains in force.

Release 01: application `3faad95` and tracking `38beb8d` push successfully. `response.loaded_version` confirms the full release, and remains unchanged after comparison. The fallback correction passes its paired views; four content destinations and the settled search/return regression pass. Private evidence label: `daily-run-2026-10-05`. Initial transient search observations are superseded by the completed navigation, without being counted as passes. Release 02 contains the missing-record wrapper correction and safe tracking records. Loaded `95a4f65` confirms it before and after comparison. Search placement, status, content, recovery/footer navigation, search/return, required assets and complete desktop/narrow views pass. E01 completes; differing random backgrounds remain recorded.

| Daily release | Change IDs | Commits | Loaded / result |
| --- | --- | --- | --- |
| 01 | 008-04 | `3faad95`, `38beb8d` | `38beb8d`; fallback placement and affected navigation pass. Illustration unavailable. |
| 02 | 008-05 | `f1a4960`, `95a4f65` | `95a4f65`; wrapper correction and all E01 checks pass. |

P08 review on loaded `95a4f65` confirms all available section content and filters, fresh bookmarks and keyboard/pointer selection, default and filtered/paged search return, seventeen internal destinations and return, required images/fonts and matching public script bytes. Fourteen complete section states are visually compared through the footer. The full CV matches every byte and all eleven pages; HEAD and valid range responses agree. Both unsatisfied requests return the expected status, but their error response metadata differs. Keep that difference for review. External publication destinations pass; a variable header-only redirect is resolved by matching native-browser article destinations and content. No profile code correction is claimed, and the whole URL remains pending. Private evidence label: `daily-run-2026-10-05`.
