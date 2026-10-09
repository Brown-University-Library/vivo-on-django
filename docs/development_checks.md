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

The runner selects prototype mode before loading the private environment. Tests choose other modes and supply made-up responses as needed. Preserve tests that protect live parsing, rendering, source failures, and formats, even when their setup uses replay. Real connectivity is checked separately.

## Check changed Python files

Run Ruff checking and formatting checks on changed Python files. Use Pylance with the project's interpreter/settings, or Pyright if Pylance is unavailable. Fix reported problems rather than suppressing them.

For a temporary missing helper package, use `uv run --no-project --with PACKAGE python SCRIPT ARGS`. Keep it out of the application's declarations.

## Check affected pages and responses

Cover what changed: rendered content, navigation/history, filters, formats, download bytes/headers, missing records, source failures, and static assets. Keep made-up names and records in repository examples; real data stays outside Git.

For layouts, inspect desktop/narrow views through the footer. Keep current font files and normal browser behavior. Status codes, text, or image hashes alone cannot establish visual agreement.

Before reusing earlier comparisons, check current code, source content, assets, viewport, fonts, and control state. Record new observations for changed areas. This is regression work for the current request, not a continuation of retired batches.

## Use the retained comparison tool

[Browser comparison](browser_comparison.md) explains commands and file/network behavior. The tool can capture a reference, compare pages, and check its detector. Generated files remain outside Git.

Former source capture commands and the validator script are archived. Existing offline inputs can still be read; [recorded responses](recorded_responses.md) documents their format. [The review note](code_retirement_review.md) explains shared code that remains.
