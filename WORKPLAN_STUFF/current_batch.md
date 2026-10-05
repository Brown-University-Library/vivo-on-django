# Current batch: twenty URLs

Batch: url-batch-008, October 5, 2026. Follow [workplan.md](workplan.md), [next_batch.md](next_batch.md), and [../AGENTS.md](../AGENTS.md). The initial list contains seventeen carried URLs and three added URLs. After three more whole cases finish, the refilled next list contains sixteen carried URLs and four added URLs. Exact pairs and evidence stay in `../../url_batch_008/` and `../../current_urls.local.md`, outside Git. The preceding [implementation](previous_workplan_artificts/url_batch_007_current_batch.md), [selected list](previous_workplan_artificts/url_batch_007_next_batch.md), and [evaluation](previous_workplan_artificts/url_batch_007_evaluation.md) are archived.

Contents:

- [Status](#status)
- [Changes and deployed checks](#changes-and-deployed-checks)
- [Local validation](#local-validation)
- [Remaining work](#remaining-work)

## Status

The owner deployed `88fb8e4`. Both preceding expanded-filter corrections pass after static collection and a browser refresh without cached resources. Terms of Use, History and Visualization Help complete four functional and two visual checks each; whole cases advance from nine to twelve. P03, Roadmap and Publications Help subsequently complete their defined checks, bringing the total to fifteen. Endpoint families and owner acceptance remain pending.

The new collected-file check passes its local tests and detects stale local copies when run as a management command. It and the institution-page correction await deployment on `main`. Application commits are `fb860ad` (collected-file checks) and `2d2fad0` (institution page); the private checkpoint records the final tracking commit and confirmed push. A push does not establish deployment or increase deployed pass totals.

## Changes and deployed checks

| Change ID | Change and reason | Local evidence | Required check after deployment |
| --- | --- | --- | --- |
| url-batch-008-01 | Add a deployment-only check for missing, unreadable or stale collected application CSS/JavaScript. Earlier rendered pages request current version queries while the web server still supplies previous copies. Document static collection after every update. | Five focused checks cover matching copies, missing/stale copies, configured source overrides, missing configuration/sources and deployment-only registration. The check reads files without requesting services or changing data. | Run static collection and `check --deploy --tag staticfiles` from the application checkout. It must pass with current copies. Confirm the actual served bytes and affected filters separately; directory mapping and browser caches remain separate checks. |
| url-batch-008-02 | Clarify complete interactive screenshot coverage and settled dialog observations. Verify the selected tab, actual bitmap size, scroll position zero and footer coverage. | Corrected paired captures and exact named-dialog records replace observations made at the wrong scale, scroll position or animation state. | Apply these checks during every affected browser comparison. Incorrect captures must not increase visual pass totals. |
| url-batch-008-03 | Render the additional institution information page in source modes, preserve no-slash/slash entry, use the shared public styles and keep existing profile/individual links local with any mount prefix. Match the reference punctuation. | Route/template tests cover both forms in prototype/prepared/replay/live modes and prefixed links. Local browser rendering confirms the heading, public styles and local destinations. | Confirm direct/slash entry, full content, four internal destinations, search/return and full desktop/narrow views. Reconcile the illustration that fails on the reference and local pages. |

## Local validation

- Full Django suite: 289 tests pass, including five new deployment checks.
- Ruff lint and formatting pass for all eight changed Python files.
- Pyright uses the project interpreter, Python 3.12 and basic checking: zero errors or warnings in all eight changed files.
- The management command detects 22 stale/missing local copies and gives the documented collection hint; the matching-copy test passes. No local collection is needed for this validation.
- Tracking files, relative links, selected counts and `git diff --check` are checked before pushing.
- Required images load in the signed-in browser; current public page styles, scripts and fonts have supporting delivery evidence. Unused CSS references and unauthenticated portrait redirects remain distinct from required browser resources.

## Remaining work

P03 completes all six functional criteria and twelve full section views. Actual return after selecting two filters and paging preserves the originating search. Its CV bytes, all five pages and signed-in HEAD/range responses pass. The owner enables Console pasting manually; permitted read-only PDF and supporting search JSON checks then run successfully. Long JSON titles pass on keyword and browse search. Roadmap and Publications Help each pass four functional and two visual criteria, including all six Publications anchors.

Search count/order, organization membership and homepage book ordering remain different; source alignment is unconfirmed. Other carried profiles retain explicit pending sections, links, interactions and documents. The Brown page is implemented locally but its deployed views and navigation remain pending. Brave blocks both route forms; do not treat a browser block as a measured application response. The three replacements require the complete criteria in [next_batch.md](next_batch.md). Every required endpoint eventually needs visual confirmation. The separate Manager and the deferred Research Areas download correction remain outside this batch. The before-script/source restriction remains in force.
