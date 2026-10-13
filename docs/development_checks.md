# Checks for application changes

## Contents

- [Run the automated tests](#run-the-automated-tests)
- [Check changed Python files](#check-changed-python-files)
- [Check local error email](#check-local-error-email)
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

## Check local error email

The `/error_check/` view raises an intentional exception when `DEBUG=True`. Django shows its error page and sends one administrator email through the `django.request` logger. With `DEBUG=False`, this endpoint returns 404 and sends no email. Other request errors can send administrator emails in either mode.

1. Set these values in the private `../.env` for a local SMTP listener:

   ```dotenv
   DJANGO_DEBUG="true"
   ADMINS_JSON='[["Local administrator", "admin@example.com"]]'
   SERVER_EMAIL="errors@example.com"
   EMAIL_HOST="localhost"
   EMAIL_PORT="1026"
   EMAIL_USE_TLS="false"
   ```

2. Start the listener in another terminal:

   ```bash
   uv run --no-project --python 3.12 --with aiosmtpd -m aiosmtpd -n -c aiosmtpd.handlers.Debugging --listen localhost:1026
   ```

   This prints received messages in that terminal; it does not deliver them to an inbox.

3. Restart `runserver` to load the environment, then open <http://127.0.0.1:8000/error_check/> once. Expect HTTP 500, the intentional exception page, and one message in the SMTP terminal containing the traceback. A 500 response alone does not confirm email delivery.

If there is no message, check the settings in the running process: `ADMINS` must contain a recipient, and the SMTP host, port, and TLS settings must match the listener. Django's error-email handler silently ignores delivery failures. This app reads `DJANGO_DEBUG`; `DEBUG_JSON` has no effect. Exported shell values override `.env`, and changing `.env` requires a process restart.

## Check affected pages and responses

Cover what changed: rendered content, navigation/history, filters, formats, download bytes/headers, missing records, source failures, and static assets. Keep made-up names and records in repository examples; real data stays outside Git.

For layouts, inspect desktop/narrow views through the footer. Keep current font files and normal browser behavior. Status codes, text, or image hashes alone cannot establish visual agreement.

Before reusing earlier comparisons, check current code, source content, assets, viewport, fonts, and control state. Record new observations for changed areas. This is regression work for the current request, not a continuation of retired batches.

For report changes, run `uv run ./run_tests.py vivo_app -v`. Report tests cover JSON validation, trusted server access, mounted links, CSV/XML bytes and cells, source ordering and failures, timeout behavior, and generation shared by separate worker processes. They use temporary files and made-up records. For live comparisons, identify each URL as Rails or Django, retain real files outside Git, and set the Django report timeout to zero. Compare the list through the footer at desktop and narrow widths and compare both formats for every configured report. Same-input Ruby/Django comparisons separate export differences from changes in source data.

Public display downloads also have focused tests in `vivo_app.tests.test_display_exports` and `vivo_app.tests.test_display_cache`. They check suffix/query forms, slash aliases, attachment headers and contents, member ordering across twenty-record batches, missing and malformed records, empty organizations, shared CSV/XML generation, fixed expiry, and separate public/report cache entries and locks. Public downloads must work without report definitions or staff attributes; protected reports must continue rejecting unauthorized requests.

For public download comparisons, set `REPORT_CACHE_TIMEOUT_SECONDS=0` in the comparison environment and restart Django; this also disables its protected-report cache. Compare both formats for a faculty member, a verified organization, a configured team, and a custom organization. Check actual CSV rows and XML worksheets/cells, not only status codes. Restore the prior timeout and restart afterward, then verify that repeated requests for both formats reuse the completed export. Keep actual downloads and source records outside Git. A deployed browser check must use the configured application prefix and an authenticated session while the installation-wide testing restriction remains in place.

## Use the retained comparison tool

[Browser comparison](browser_comparison.md) explains commands and file/network behavior. The tool can capture a reference, compare pages, and check its detector. Generated files remain outside Git.

[The review note](code_retirement_review.md) identifies remaining maintenance decisions. The comparison tool reads its own page captures; application tests use made-up source responses.
