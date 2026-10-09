# vivo-on-django

## Brief overview

This Django webapp serves Researchers@Brown searches, researcher and organization pages, visualizations, downloads, and existing public links. Developers use this repository to run and maintain the application.

## More info

- [Brief overview](#brief-overview)
- [More info](#more-info)
- [Local installation](#local-installation)
- [Usage](#usage)
- [Tests](#tests)
- [Primary dependencies](#primary-dependencies)

The owner completed the conversion review after the v1.0 release. [Public behavior](docs/public_behavior.md) describes what to preserve. [Source configuration](docs/source_journey.md) explains Solr, images, documents, graph data, VIVO representations, and the separate homepage book database. The webapp uses these existing services; it does not provision them or rebuild Manager or VIVO.

Use [the documentation index](docs/docs_README.md) for current guides. [Conversion history](historical_conversion_info/README.md) preserves selected methods and decisions. Earlier batch statuses are historical. Prepared mode is a build artifact slated for gradual removal; [code retained for review](docs/code_retirement_review.md) explains the shared helpers that need attention during cleanup.

## Local installation

Install Git and uv, and arrange access to the repository. uv manages the interpreter specified by [pyproject.toml](pyproject.toml).

1. Start in the parent directory where you want the checkout and its local support files:

   ```bash
   mkdir vivo_on_django_stuff
   cd vivo_on_django_stuff
   git clone https://github.com/birkin/vivo-on-django.git vivo-on-django
   cd vivo-on-django
   ```

2. Install the locked packages and create the local database, cache, and log directories:

   ```bash
   uv sync --locked
   mkdir -p ../DBs ../cache_dir ../logs
   ```

   This may download packages and the interpreter. uv creates `.venv` inside the checkout. Local data and configuration stay beside the checkout.

3. Create or update `../.env` in your editor. Preserve existing values you need. This minimum configuration starts the retained local sample mode without contacting research-data services:

   ```dotenv
   DJANGO_SECRET_KEY="replace-with-your-local-development-secret"
   DJANGO_DEBUG="true"
   ALLOWED_HOSTS_JSON='["localhost", "127.0.0.1"]'
   STATIC_URL="/static/"
   STATIC_ROOT="../staticfiles"
   PAGE_DATA_MODE="prototype"
   TURNSTILE_ENABLED="false"
   ```

   [example.env](example.env) documents the available keys, but its `PAGE_DATA_MODE="prepared"` requires an external bundle. Use the settings above to serve sample content from a standalone checkout. `ALLOWED_HOSTS_JSON` is a JSON list; `STATIC_URL` is a browser URL prefix; `STATIC_ROOT` names a local output directory relative to the command's working directory.

   [config/settings.py](config/settings.py) uses python-dotenv to find the nearest `.env` starting beside the settings module and searching parent directories. A `.env` inside the checkout can take precedence over `../.env`; exported shell values take precedence over file values.

4. Create or update Django's local tables:

   ```bash
   uv run ./manage.py migrate
   ```

   This writes `../DBs/db.sqlite3`. It does not populate research records or change a Solr index. If SQLite cannot open its file, check that `../DBs` exists and is writable.

## Usage

From the checkout, start the local development server:

```bash
uv run ./manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/>. Stop the server with Ctrl+C. Keep `DJANGO_DEBUG=true` for ordinary local static-file serving. Local logs and cached responses use `../logs/django.log` and `../cache_dir`. After changing `.env`, stop and restart the server so it reads the new values.

For current research data, select `PAGE_DATA_MODE=live` and configure the sources described in [source configuration](docs/source_journey.md). Live mode contacts those sources while serving requests. Homepage books also need PyMySQL; install it locally with `uv sync --locked --group staging`, then start the server with `uv run --locked --group staging ./manage.py runserver 127.0.0.1:8000`. The staging group also includes Pillow. A plain `uv sync --locked` removes packages from unselected groups; include the groups you still need when syncing.

This setting supplies sample content for local use and tests. It does not demonstrate live integration. Some retained paths return placeholder text.

Legacy prepared and replay code still reads external saved files. Missing inputs produce errors rather than live requests. The [older data-mode guides](docs/docs_README.md) remain for existing setups during cleanup; source-response capture commands and the standalone recording validator have been retired.

For optional browser comparisons, see [development checks](docs/development_checks.md) and [developer tools](tools/tools_readme.md).

## Tests

Run all discovered tests from the checkout:

```bash
uv run ./run_tests.py
```

To show each app test's name and description:

```bash
uv run ./run_tests.py vivo_app -v
```

Complete the local configuration steps first; the runner still needs `ALLOWED_HOSTS_JSON` and `STATIC_ROOT`. It selects sample content and `/static/` before loading the private environment. Individual tests override the mode and use made-up source responses. Django creates and removes its test database. These tests do not verify connectivity to real services.

The suite runs with the base dependencies. Its Pillow image check skips when Pillow is absent; include it with `uv run --locked --group local ./run_tests.py`. The suite does not launch Playwright browsers. See [development checks](docs/development_checks.md) for focused test selection and Python checks.

## Primary dependencies

This list follows declarations in [pyproject.toml](pyproject.toml), imports/configuration, and supporting packages in [uv.lock](uv.lock). There is no separate requirements file.

| Package | Purpose and where it is used |
| --- | --- |
| `Django` | Requests, templates, sessions, tests, and database tables in `config/` and `vivo_app/`. |
| `python-dotenv` | Environment loading in `config/settings.py`. |
| `httpx2` | Source and Turnstile HTTP requests in [source_requests.py](vivo_app/lib/source_requests.py) and [bot_detect.py](vivo_app/lib/bot_detect.py). |
| `django-browser-reload` | Local reload support configured in `config/settings.py` and `config/urls.py` when both `DJANGO_DEBUG` and `DJANGO_BROWSER_RELOAD` are enabled. Declared in the base dependencies. |
| `pymysql` | Separate live homepage book database in [source_books.py](vivo_app/lib/source_books.py); supplied by staging and prod. Django's own database uses SQLite. |
| `playwright`, `pillow` | Browser and image comparisons in [compare_sites.py](tools/compare_sites.py); Playwright is in local, Pillow in local and staging. Pillow also supports the image check in `vivo_app/tests/test_comparison.py`. |

`trio` is also directly declared, but no direct application import was found. Review asynchronous backend use and package requirements before removing it; see [the review note](docs/code_retirement_review.md).

The lockfile records supporting packages, including Django's `asgiref` and `sqlparse`, and the HTTP client's `anyio`, `httpcore2`, and `truststore`. Keep the local, staging, and prod groups when reviewing dependencies. Ruff is configured in [ruff.toml](ruff.toml) and supplied separately; tests use Django and unittest. Pylance or Pyright checks changed Python files and is also supplied separately. This inventory does not establish that an unconfirmed dependency is safe to remove.
