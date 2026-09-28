# Documentation directory

This directory holds the Django replacement's scope decisions, local data and source guides, and comparison notes. The repository's [goal](../GOAL.md) defines the overall outcome; the files below explain particular parts of the work.

- [conversion/](conversion/index.md) — Browser-comparison instructions and recorded visual findings from the conversion work.
    - [conversion/browser_comparison.md](conversion/browser_comparison.md) — How to capture and compare selected public and Django pages in a browser.
    - [conversion/index.md](conversion/index.md) — Entry point for the conversion comparison guides and findings.
    - [conversion/visual_comparison_findings.md](conversion/visual_comparison_findings.md) — Recorded homepage and organization screenshot differences and their follow-up.
- [docs_README.md](docs_README.md) — This overview and list of the directory's contents.
- [fonts.md](fonts.md) — Font files, licenses, and browser behavior needed to match the public pages.
- [future_branch_cleanup.md](future_branch_cleanup.md) — Items to review for possible cleanup after the replacement is accepted.
- [prepared_data.md](prepared_data.md) — How saved page data supports local development without contacting source services.
- [public_endpoint_scope.md](public_endpoint_scope.md) — Approved public URLs, their required behavior, and their data sources.
- [recorded_responses.md](recorded_responses.md) — How saved upstream responses are validated and used for offline replay.
- [routes_mapping.md](routes_mapping.md) — Earlier Rails-to-Django route notes; use the current scope document for required behavior.
- [server_setup.md](server_setup.md) — Guide for the first development-server installation and its configuration.
- [source_journey.md](source_journey.md) — Live and replay source processing for search, profiles, organizations, graphs, and other selected responses.
