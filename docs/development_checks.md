# Checks for application changes

## Contents

- [Run the automated tests](#run-the-automated-tests)
- [Check changed Python files](#check-changed-python-files)
- [Check affected pages and responses](#check-affected-pages-and-responses)
- [Use the retained comparison tool](#use-the-retained-comparison-tool)

## Run the automated tests

Run commands from the repository root:

```bash
uv run ./run_tests.py
uv run ./run_tests.py vivo_app -v
uv run ./run_tests.py vivo_app.tests.test_source_pages -v
```

The first discovers the complete suite. The second selects the app and shows each test's name, description, and result. The third selects a module; dotted class/method names narrow it further. Django creates and removes its test database. Failures produce a nonzero exit status.

The runner selects made-up source settings before loading the private environment and rejects unexpected network connections. Tests provide source responses to the application parsers and rendering code. Preserve tests for parsing, rendering, source failures, and formats. Real connectivity is checked separately.

## Check changed Python files

Run Ruff checking and formatting checks on changed Python files. Use Pylance with the project's interpreter/settings, or Pyright if Pylance is unavailable. Fix reported problems rather than suppressing them.

For a temporary missing helper package, use `uv run --no-project --with PACKAGE python SCRIPT ARGS`. Keep it out of the application's declarations.

## Check affected pages and responses

Cover what changed: rendered content, navigation/history, filters, formats, download bytes/headers, missing records, source failures, and static assets. Keep made-up names and records in repository examples; real data stays outside Git.

For layouts, inspect desktop/narrow views through the footer. Keep current font files and normal browser behavior. Status codes, text, or image hashes alone cannot establish visual agreement.

Before reusing earlier comparisons, check current code, source content, assets, viewport, fonts, and control state. Record new observations for changed areas. This is regression work for the current request, not a continuation of retired batches.

For report changes, run `uv run ./run_tests.py vivo_app -v`. Report tests cover JSON validation, trusted server access, mounted links, CSV/XML bytes and cells, source ordering and failures, timeout behavior, and generation shared by separate worker processes. They use temporary files and made-up records. For live comparisons, identify each URL as Rails or Django, retain real files outside Git, and set the Django report timeout to zero. Compare the list through the footer at desktop and narrow widths and compare both formats for every configured report. Same-input Ruby/Django comparisons separate export differences from changes in source data.

## Use the retained comparison tool

[Browser comparison](browser_comparison.md) explains commands and file/network behavior. The tool can capture a reference, compare pages, and check its detector. Generated files remain outside Git.

[The review note](code_retirement_review.md) identifies remaining maintenance decisions. The comparison tool reads its own page captures; application tests use made-up source responses.
