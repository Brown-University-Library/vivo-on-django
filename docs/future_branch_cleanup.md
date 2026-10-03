# Possible cleanup after the public-site replacement

This is a review list, not a decision to remove files. The current goal is to finish and verify the Rails-to-Django replacement. After the owner accepts it and the new site has run long enough to expose ordinary usage and less common records, review each item below against the code and operations in use at that time. Update this list as the conversion changes.

## What should remain

Keep the Django code that serves required URLs, templates, static files, migrations, runtime settings, dependency declarations, and instructions needed to run and maintain the website. In particular, Solr access is part of the intended live website. `SOLR_URL`, the live source request and response processing under `vivo_app/lib/source_*.py`, and other source connections must remain wherever the accepted pages use them.

Keep useful automated tests, including tests built from made-up records. Tests do not serve visitor requests, but they help maintain the live code safely. If a deployment package should contain only runtime files, exclude development material when building that package rather than removing it from `main` solely to shrink the package. Keep a durable record of conversion decisions and evidence in Git history or a separate archive before removing historical documents from `main`.

## Items to review for removal from `main`

| Current files or settings | Condition for removal or consolidation |
| --- | --- |
| `WORKPLAN_STUFF/workplan.md`, its checklists and batch records, `WORKPLAN_STUFF/previous_workplan_artificts/`, `codex-plan.md`, this cleanup list, and historical route notes such as `docs/routes_mapping.md` | The owner has accepted the replacement, outstanding work has moved to normal maintenance tracking, and decisions worth keeping have been recorded in a concise maintainer guide or archive. Preserve `WORKPLAN_STUFF/GOAL.md` or its current successor while it still explains required behavior. |
| `docs/conversion/`, `docs/prepared_data.md`, `docs/recorded_responses.md`, and conversion portions of `docs/source_journey.md` | Comparison and offline development procedures are no longer needed for routine maintenance. Keep any instructions still needed to diagnose live source requests. |
| `tools/compare_sites.py`, `tools/source_capture.py`, `tools/validate_recordings.py`, and `vivo_app/management/commands/capture_solr_journey.py` | The team has decided it no longer needs those capture and comparison commands for regression checks or later source changes. Remove their command-specific tests and development dependencies only after checking other uses. |
| `PAGE_DATA_MODE=prototype`, sample-data helpers in `vivo_app/lib/display.py`, `vivo_app/lib/home.py`, and `vivo_app/lib/visualization.py`, plus sample-only templates or settings | Every required page uses accepted live or otherwise intentional production data, and no retained route or test needs the sample path. Keep any helper that also serves live pages. |
| `PAGE_DATA_MODE=prepared`, `PREPARED_FIXTURE_DIR`, `vivo_app/lib/prepared_data.py`, `vivo_app/management/commands/validate_prepared_data.py`, and prepared-only routes, templates, tests, and documentation | The prepared bundle is no longer used for a supported offline preview, recovery, or comparison workflow. First identify shared validation and rendering functions that live pages still import. |
| `PAGE_DATA_MODE=replay`, `UPSTREAM_RECORDING_MANIFEST`, `UPSTREAM_RECORDING_CASE`, and `vivo_app/lib/recorded_responses.py` | The team has deliberately retired raw-response replay. First move any request types or validation helpers still used by live source processing or retained tests. |
| Conversion-specific settings in `example.env` and conversion entries in `AGENTS.md` and `README.md` | The corresponding modes and commands have actually been removed. Rewrite current setup instructions to describe the accepted live application. |

This list identifies candidates, not complete dependency chains. Before deleting one, search imports, routes, settings, templates, commands, tests, and deployment configuration; remove or replace each reference in the same change. Run application tests and a representative live-site comparison. Keep the removal review separate from the conversion acceptance decision.

## How much offline source data is needed

Solr supplies current search and record data to the live site. Prepared page data supplies already-arranged fields for selected offline layout work. Raw-response recordings let the same Django processing run offline for exact saved requests. Neither offline format is a plan to copy the full Solr index or every research record.

With direct access to the actual Solr index, use small, paced live checks for new records and queries. Keep a representative saved set for repeatable checks of filters and pagination, sparse and full profiles, organization membership, downloads, graphs, unavailable records, and relevant error behavior. Reuse a response when it covers a new check; add one when a specific mismatch or an offline test calls for it. The acceptance checks must also exercise live requests outside the saved set. More recordings alone cannot prove that arbitrary live requests work.

Keep real records, response bodies, screenshots, and reports outside Git. Those external materials need their own retention and access decision; removing conversion code from `main` does not remove those copies.
