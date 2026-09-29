# AGENTS.md — vivo-on-django Repository Instructions

This file defines the canonical coding directives for this repository.

Adapted from the [script_project template](https://github.com/birkin/birkin_coding_tools/blob/main/script_project/AGENTS.md).

Keep this `AGENTS.md` file at no more than 300 lines, counting blank lines and the final `---`. When adding guidance, shorten or remove repeated material first; keep repository-specific instructions and the project index useful.

General coding directives are appropriate here when they help different developers and agents follow consistent conventions, since contributors may not share global instructions. Keep useful shared guidance within the 300-line limit.

If other instruction files exist (Copilot, IDE rules, contributor docs) and conflict with this file, follow this file and treat the others as stale.


## Table of contents

- [Project basics](#project-basics)
- [How to run code](#how-to-run-code)
- [Coding directives (Python)](#coding-directives-python)
- [Django architecture conventions](#django-architecture-conventions)
- [Front-end change guidance](#front-end-change-guidance)
- [Tests](#tests)
- [Change workflow expectations](#change-workflow-expectations)
- [Privacy and publication](#privacy-and-publication)
- [If instructions are missing or ambiguous](#if-instructions-are-missing-or-ambiguous)
- [Agent project index](#agent-project-index)


## Project basics

- Purpose: reproduce the existing public Researchers@Brown Rails application's URLs, behavior, and appearance in Django, as defined in `GOAL.md`.
- Primary language: Python; framework: Django 5.2.
- Target runtime: Python 3.12 (`pyproject.toml` requires `>=3.12,<3.13`).
- Dependency / execution tool: `uv`
- The only dependency groups in `pyproject.toml` are `local`, `staging`, and `prod`. `local` is for laptop-only tools; `staging` is for the development server; `prod` is for the production server. Do not add a `dev` group: `uv sync` and `uv run` install it by default, including on the development server.
- The repository root contains this file, `.git/`, `manage.py`, and `pyproject.toml`. The enclosing workspace contains separate repositories and local support files.
- `GOAL.md` defines current scope. Older plans and route inventories are historical references; they do not require rebuilding unused features or the separate Manager application.


## How to run code

- Assume user is in the project-root directory.
- Use `uv` to run Python code; do not invoke `python` or `python3` directly.
- Install the locked dependencies with `uv sync --locked`; use the repository's `.venv` interpreter.
- Run a script via: `uv run ./path_to_script.py --help`
- Run tests via: `uv run ./run_tests.py`. This discovers all tests.
- Run the local Django app tests via: `uv run ./run_tests.py vivo_app -v`.
- Pass a dotted module, class, or method name for a smaller selection, for example: `uv run ./run_tests.py vivo_app.tests.test_home -v`. The runner's docstring includes examples; `-v` or `--verbose` shows each test's name, docstring, and result.
- `run_tests.py` initializes Django and uses its configured test runner, including test database setup and cleanup. It uses `config.settings` unless `DJANGO_SETTINGS_MODULE` is already set, runs without interactive prompts, and exits with a nonzero status when tests fail.
- Keep the full test suite runnable with the application's base dependencies. Playwright belongs in `local`; Pillow is in `local` and `staging` for image comparison checks. Tests may skip only their tool-specific checks when these packages are absent.
- Run Django management commands via: `uv run ./manage.py THE-COMMAND`.
- For a standalone helper needing a missing package, use `uv run --no-project --with PACKAGE python SCRIPT ARGS`. Do not add temporary helper dependencies to `pyproject.toml` or install them globally.


## Coding directives (Python)

### Type hints and imports

- Use Python 3.12 type hints everywhere (functions and important variables). (Unless a `pyproject.toml` specifies a different version.)
- Prefer builtin generics (e.g., `list[str]`, `dict[str, int]`) over `typing.List` / `typing.Dict`.
- Prefer PEP 604 unions (e.g., `str | None`) over `Optional[str]`.
- Avoid `typing` and `annotations` imports unless strictly necessary.
- Before finishing, check every changed Python file with Pylance using the project interpreter and type-checking settings; use Pyright if Pylance is unavailable. Fix errors with simple annotations and explicit checks instead of suppressing diagnostics.

### Script structure

- Structure runnable modules as:
  - `def main() -> None: ...`
  - `if __name__ == '__main__': main()`
- Keep `main()` simple: parse args / orchestrate calls only.
- Put real logic into top-level helper functions and modules (no nested function definitions).
- Keep call chains shallow: `main()` may call a helper, which may call another helper, with one further level only when necessary.

### Functions and control flow

- Prefer single-return functions (use local variables and a final return).
- Do not define functions inside other functions.
- Favor clarity and explicitness over cleverness.

### Logging

- When adding a log statement, when possible, format variable values as a label, followed by a comma and a space, with the value enclosed in double backticks.
- Prefer a label that matches the variable name. For example: ```log.debug(f'branch_and_commit, ``{branch_and_commit}``')```

### HTTP and networking

- Use `httpx2` for application HTTP calls and new HTTP helpers. Add it as a dependency when source-client implementation begins.
- Do not introduce alternate HTTP libraries (e.g., `requests`, `aiohttp`) unless the repository already depends on them and there is a documented reason.

### Docstrings

- Use triple-quoted docstrings.
- Write docstrings in present tense, with triple-quotes on their own lines.
  - Good:
    ```
    """
    Parses ...
    """
    ```
  - Avoid: `"""Parse ..."""`
- The last line of non-test function-docstrings should be: `Called by: the_caller_function()` (or, if in another class/module, `Called by: module.Class.the_caller_function()`)
- Start test-function docstring-text with "Checks..."
- For header-comments, in functions, start the comment with two hashes (e.g., `## does this`).

### Additional coding directives

- Inspect `ruff.toml` for formatting settings: Python 3.12, 125-character lines, four-space indentation, and single quotes. Keep Ruff's target version aligned with the runtime requirement in `pyproject.toml`.

### Markdown formatting

- Do not use hard line-breaks in markdown files; let paragraphs wrap naturally.
- When creating a Markdown file with more than three top-level `##` headings, add a table of contents near the top with links to those `##` headings.
- Use plain, direct language. Explain who does what, in what order, and why; describe command behavior and failure recovery with concrete actions.
- Say "made-up names and records in repository examples; real data stays outside Git" instead of "invented and non-identifying examples."


## Django architecture conventions

### View-layer responsibilities

- Use function-based views for application code. Existing Django authentication and admin routes are framework integrations; do not rewrite them solely to apply this convention.
- Keep application endpoint functions in `vivo_app/views.py`; existing authentication endpoints live in `vivo_app/views_auth.py`.
- Register application endpoints in `config/urls.py`. Error handlers are registered there separately. Put new reusable helpers in `vivo_app/lib/`, not in view modules.
- Views should coordinate these steps:
  - Parse request input (query params, POST body, files)
  - Perform minimal validation and shaping of inputs
  - Delegate substantive work to modules under `vivo_app/lib/`
  - Convert returned results into the appropriate `HttpResponse` (HTML, JSON, redirects)

### Business logic placement

- Put domain logic, integrations, and reusable operations in `vivo_app/lib/`.
- Keep conversion-only capture, validation, and browser comparison logic in `tools/`. A Django management command may remain as a small entry point for a tool.
- If multiple endpoints share logic, move that shared logic into `vivo_app/lib/` and keep each view focused on handling the request and response.
- Prefer testable functions in `vivo_app/lib/` that accept plain Python values; pass Django request objects only when necessary for a specific reason.

### Imports and dependencies

- `views.py` should primarily import:
  - Django primitives (`HttpRequest`, `HttpResponse`, `render`, `redirect`, etc.)
  - The minimal set of functions/classes from `vivo_app/lib/` needed for each endpoint
- Place new view helpers in `vivo_app/lib/`; shared rendering helpers, including `render_or_stub()`, live in `vivo_app/lib/page_rendering.py`.


## Front-end change guidance

- When front-end changes are required, use JavaScript only where it is truly required.
- Prefer updates in CSS, Python code, or Django template code when those can satisfy the behavior or presentation need.


## Tests

- Use Django's test framework for application tests and standard library `unittest` for independent helpers; do not introduce pytest.
- `vivo_app/tests/` checks routes, home and static pages, display pages, and publications using local or sample data. Django's runner creates and destroys its test database.
- New behavior should usually come with a focused test covering:
  - the happy path
  - at least one failure / edge case


## Change workflow expectations

- For every user prompt, append the prompt and a concise summary of the resulting work or answer to `../PROMPTS.md`, with a local timestamp. Treat it as an archive: do not maintain its contents list. Keep it outside Git and update it efficiently without rereading the whole file unless older context is needed.
- The owner prefers Sol with High reasoning for routine work. Flag a concrete reason to consider Astra with Extra-high reasoning when a task or unresolved problem would benefit; do not switch models automatically.

When implementing a change (especially from an issue/task):

1. Read relevant surrounding code and match existing conventions.
2. Make the smallest correct change that satisfies the request.
3. Update tests when behavior changes and run `uv run ./run_tests.py`. For local page changes, use `uv run ./run_tests.py vivo_app -v`.
4. Before finishing significant new code or changes, run `ruff check` and `ruff format --check` on the changed Python files, then check those files with Pylance using the project's `.venv` interpreter and type-checking settings. Use Pyright if Pylance is unavailable. Fix warnings and errors instead of suppressing diagnostics. If a check cannot run, report what prevented it and the concrete command or setup needed.

### Issue-based work and review

- Work directly from the current user request. Issues, formal templates, labels, preliminary discussions, and decision comments are not prerequisites for authorized local work.
- When issue-based work is authorized, organize each issue around one clear outcome and create a branch for its file changes. Include the issue number and a short description in the branch name, and record it in work reports. A request to change local files does not by itself authorize creating an issue or posting comments.
- Save requested plans, documentation, and code changes locally, leaving them uncommitted for the user's review unless the user explicitly requests a commit. Preserve the user's manual edits during revisions.
- Report the files changed, checks actually performed, and anything needing review. Distinguish work ready for review from work accepted by the user, and distinguish local, committed, and pushed changes. Link existing issues, commits, and pull requests when relevant.
- Keep the issue open for review and iteration. A finished draft or implementation report does not mean the user has accepted the work or wants the issue closed.

### GitHub attribution

- Every GitHub post or text update must visibly identify Codex as the agent that created or edited it. This includes issue descriptions, pull-request descriptions, comments, reviews, and discussions; do not rely on the displayed account name to convey authorship.
- Begin new issue descriptions with `Created by Codex at the user's request.` Keep this attribution separate from the user's prompt. For other posts or edits, use an accurate visible attribution such as `Posted by Codex` or `Edited by Codex`; begin issue comments with `Codex response` as described below.
- Distinguish who posted the material from who wrote it: identify quoted prompts as the user's words, and identify Codex's summaries, proposals, and reports as Codex's work.

### Issue bodies and user prompts

- For repository posts, write a fresh, minimal summary of the requested behavior, changes, and checks. Do not paste private conversation excerpts, raw logs, tracebacks, configuration, commands, or tool output. Apply [Privacy and publication](#privacy-and-publication) before posting.
- When asked to draft an issue instead, use **Goal** for the intended outcome, **Context** for relevant background and constraints, and **Tasks** for the requested actions. Make clear whether the user wants advice, a plan, documentation, or implementation. Add **Completion criteria** only when observable checks would clarify what counts as done. Keep the structure proportional to the work.
- Use a structured body argument when available, or a temporary file with `--body-file` when using `gh`. After posting or editing, fetch the issue and verify the sanitized body and visible attribution. Return the issue link.

### GitHub issue comments

- Post a comment only when the user asks or has already authorized it. Authorization to maintain prompt and work records for an issue can cover later updates within that scope. A request to implement a change does not by itself authorize a comment, and a request to comment does not by itself authorize implementation or commits.
- Before posting, read the target issue, all its comments, and applicable `AGENTS.md` files. Address the current request within its stated scope; use newer maintainer guidance to resolve older conflicting comments.
- Begin comments with `Codex response` and identify the response type, such as **answer**, **advice**, **proposal**, **prompt record**, or **implementation report**. Clearly distinguish an agent proposal from an accepted maintainer decision.
- Keep private prompt records local. An authorized repository comment should summarize the requested work in fresh, sanitized wording rather than quoting the private conversation.
- Use authorized comments to record substantive prompts and work at useful milestones; every local exchange does not need a GitHub update. Implementation reports should describe what changed, what was verified, any remaining work or review, and whether changes are local, committed, or pushed. Posting a report does not authorize a commit or issue closure.
- Use a structured comment-body argument when available. If using `gh`, put multiline Markdown in a temporary file and pass it with `--body-file`. Verify the posted text and return its direct link. If a posting attempt has an uncertain result, check existing comments before retrying to avoid duplicates.

### Commit authorization

- Create or amend a commit only when the user explicitly asks Codex to commit the changes in question. This applies to Git commands and equivalent tools or APIs. A request to develop a plan, implement a change, save files, create a branch, post a summary, or finish the work does not authorize a commit.
- Review approval, a suggested commit message, or the user saying they might commit the work is not an instruction for Codex to commit. Commit-message conventions describe how to write an authorized commit; they do not grant permission to make one.
- Apply an explicit commit instruction only to its stated changes and scope. Permission for an earlier task or commit does not automatically cover later revisions. Do not ask again when the current changes are already covered by clear authorization.
- If commit authorization is absent or unclear, finish the authorized local work and report that it is ready for review and uncommitted. Do not delay that work to ask whether to commit.
- Permission to commit does not by itself authorize pushing, creating or merging a pull request, or closing an issue. Follow the user's instructions for each action separately.

### Issue closure

- Only the user closes issues unless the user specifically asks Codex to close an identified issue. Keep issues open by default, even after requested work, tests, review, commits, pushes, or merges are complete. A request to finish the task or approval of a plan is not permission to close the issue.
- Without that specific request, do not close issues through the UI, CLI, API, tools, or a comment-and-close action. Do not arrange automatic closure through commit messages, pull-request descriptions, links, or automation.
- Use ordinary references such as `Refs #123` or an issue URL unless closure is authorized. Do not use closing keywords such as `Closes`, `Fixes`, or `Resolves` with an issue reference or add links that close the issue when merged. Before an authorized merge, check for existing automatic closure instructions and links; remove them if authorized or leave the merge pending if it would close an issue without permission.
- For planning work, develop and save the plan locally, post a summary if authorized, and leave the changes uncommitted and the issue open for review. Committing, continuing revisions, and closing the issue are separate decisions.

### Commit messages

- Apply these conventions only after the user has authorized a commit under [Commit authorization](#commit-authorization).
- Group related files into logical, focused commits; do not require a separate commit for every file.
- Keep each commit message brief, with no more than ten words.
- Write messages in the present tense so they complete the phrase "This commit..." Begin with a fitting verb such as "Adds," "Implements," or "Updates."


## Privacy and publication

- Apply these rules to public and private repositories, including tracked files, agent notes, issue titles and bodies, comments, pull requests, commit messages, and attachments. Permission to investigate using conversation, local files, or tool output is not permission to publish that information.
- Do not publish explicit server names, hostnames, server IP addresses, credentials, tokens, private endpoints, personal information, cookies, session data, or unreviewed browser artifacts. Use generic descriptions and relative paths or variable names instead of full local or server filesystem paths.
- Keep sensitive working notes out of tracked files. Do not publish known or suspected vulnerabilities, affected live systems, exploit steps, or details that could help someone exploit a weakness. Discuss findings privately with the user; describe repository updates in terms of the general improvement and safe validation results.
- Before every repository post or edit, review the exact outgoing text, examples, links, screenshots, and attachments for sensitive information. Check combinations of details as well as individual values. Information already present in source code or an earlier post is not automatic permission to repeat it.
- When posting is authorized and the complete content is clearly safe to publish, proceed without another approval request. If sensitivity is uncertain, prepare sanitized wording, show it in the private conversation, explain the uncertainty without repeating sensitive values, and wait for confirmation of that exact text before posting. Never use an issue or comment to ask whether sensitive information is safe to disclose.
- Keep full server filesystem paths out of documentation, examples, and agent notes. Keep all server-deployment documentation, including any mention of deployment caller scripts, outside READMEs.


## If instructions are missing or ambiguous

- Do not ask questions unless absolutely necessary to proceed.
- Make reasonable assumptions, state them explicitly, then implement.
- Do not assume permission to commit or close an issue. When that permission is absent or unclear, complete the authorized local work, leave it uncommitted, and keep the issue open as described above.
- If blocked, provide:
  - what you tried
  - what you found in the repo
  - a concrete next step (command, file to edit, or minimal decision needed)


## Agent project index

### Scope and reference material

- Start with `GOAL.md`. The running public Rails application is the reference for required behavior and appearance; historical routes and prototype tests alone do not establish current requirements.
- `codex-plan.md`, `OLD_gpt5_conversion_plan.md`, `OLD_windsurf_conversion_plan.md`, and `docs/routes_mapping.md` describe earlier, broader work. Follow `GOAL.md` when they disagree.
- When the enclosing workspace is available, `../stuff_README.md` locates its materials. `../vivo-on-rails/` contains Rails source for comparison, including `config/routes.rb`, controllers, views, and assets.
- `../rab_primary_url_paths.md` and `../apache_log_analysis.md` contain historical URL evidence. `../REPORT__previous_work.md`, `../REPORT__consolidation.md`, and `../previous_work/` supply local background. Review privately; do not copy raw records or operational details into tracked files.
- These adjacent files are not part of a standalone checkout. Some background links in `GOAL.md` refer to filenames that currently live in the enclosing workspace.

### Code locations

| Location | What to inspect there |
| --- | --- |
| `pyproject.toml`, `uv.lock`, `ruff.toml` | Runtime requirements, dependencies, older inline coding guidance, and formatting settings. |
| `run_tests.py` | Django test command, with full discovery, app/module/class/method selection, and optional verbose output. |
| `config/settings.py` | Environment loading, database, cache, logging, templates, and public-site configuration. |
| `config/urls.py` | All application routes, framework authentication routes, and error handlers; there is no app-level `urls.py`. |
| `vivo_app/views.py` | Public page handlers and older placeholder endpoints for search, visualization, exports, and editing. |
| `vivo_app/lib/display.py` | Sample display and publication data; entity types currently come from ID-prefix guesses. |
| `vivo_app/lib/home.py`, `vivo_app/lib/assets.py` | Sample book-cover pages and random homepage background selection. |
| `vivo_app/lib/visualization.py` | Visualization helpers that return local sample data. |
| `vivo_app/lib/prepared_data.py`, `vivo_app/lib/recorded_responses.py`, `vivo_app/lib/source_*.py` | Readers and processors used while Django serves prepared, replayed, or live pages. |
| `tools/`, `docs/conversion/` | Conversion checks, bounded source capture, saved-response validation command, and comparison findings. |
| `vivo_app/templates/`, `vivo_app/static/` | Page templates, shared includes, CSS, JavaScript, and images; follow the template actually selected by each view. |
| `vivo_app/context_processors.py` | Shared template values from settings. |
| `vivo_app/views_auth.py`, `vivo_app/forms.py`, `vivo_app/models.py`, `vivo_app/migrations/` | Existing authentication and profile code. Its presence does not expand conversion scope. |
| `vivo_app/tests/`, `test_visualization.py` | Django page tests and sample visualization checks. |

### Local configuration and current limitations

- Settings call `load_dotenv()` and require `ALLOWED_HOSTS_JSON`, `STATIC_URL`, and `STATIC_ROOT`. Use `example.env` for current keys and Rails counterparts; later source settings are explicitly commented out. Keep the actual `.env` outside Git.
- Local settings use `../DBs/`, `../cache_dir/`, and `../logs/`. Imports create the logs directory, but local database use requires its parent directory to exist. After relocating a checkout, verify `.venv` and use `uv sync --locked` to prepare dependencies as needed.
- Several routes return placeholders. `render_or_stub()` can return a successful text response when a template fails, so a status-code assertion alone does not prove a page renders correctly. Check content, templates, and browser behavior for affected pages.
- `?format=json` changes the response for many views; preserve confirmed query-parameter behavior. Keep individual-export URL patterns before the generic individual route.
- Homepage imagery is randomized and several helpers return sample data. Account for those differences during comparisons; passing prototype tests does not demonstrate that the public conversion is complete.

---
