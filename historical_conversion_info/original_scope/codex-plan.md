# Codex Plan

Historical record from revision `8c5c8ce`, preserved during the October 9, 2026 cleanup. The owner considers the conversion review complete. Any pending labels, acceptance instructions, or workflow directions below describe the earlier conversion; they are not current tasks.

## Fundamental Goals
- Re-read the `pyproject.toml` `llm_code_directives` before touching code so every change follows the required conventions.
- Convert the full Rails app in `OBSOLETE/` to a Django 5.2 implementation.
- Achieve endpoint parity by ensuring every Rails route has a matching Django URL and returns equivalent HTML/CSS/JS behavior.

## Current State
- Base layout now matches Rails header/footer and pulls legacy Bootstrap/theme assets.
- Home endpoint renders with carousel stubs, alias redirect, and environment-driven links.
- Static pages (about/help/faq/history/roadmap/publications/terms/help viz/brown) ported with shared search box partial.
- Tests updated; `uv run ./manage.py test -v 2` passes.

## Outstanding Follow-ups
1. Configure env vars (`GOOGLE_ANALYTICS_KEY`, `MANAGER_URL`, `BOOK_COVER_BASE_PATH`, etc.) for production parity once values are known.
2. Verify imported CSS/JS and hero imagery in the browser; trim or reorganize assets as other endpoints are ported.
3. Next parity target per plan: search endpoint (templates + helper scaffolding), followed by display refinements.
4. Capture or stub book cover images under `BOOK_COVER_BASE_PATH`; decide whether to ship local copies for offline dev.
