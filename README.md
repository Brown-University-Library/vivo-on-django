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

Use [the documentation index](docs/docs_README.md) for current guides. [Conversion history](historical_conversion_info/README.md) preserves selected methods and decisions. Earlier batch statuses are historical. [Code retained for review](docs/code_retirement_review.md) explains why some older data-mode code remains.

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

   [example.env](example.env) documents the available keys. `ALLOWED_HOSTS_JSON` is a JSON list; `STATIC_URL` is a browser URL prefix; `STATIC_ROOT` names a local output directory. `config/settings.py` loads values with python-dotenv; exported shell values take precedence.

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

Open <http://127.0.0.1:8000/>. Stop the server with Ctrl+C. Keep `DJANGO_DEBUG=true` for ordinary local static-file serving. Local logs and cached responses use `../logs/django.log` and `../cache_dir`.

For current research data, select `PAGE_DATA_MODE=live` and configure the sources described in [source configuration](docs/source_journey.md). Live mode contacts those sources while serving requests. Homepage books also need PyMySQL; install it locally with `uv sync --locked --group staging`. The staging group also includes Pillow.

Prepared and replay modes remain because live code and tests share their helpers. [Prepared data](docs/prepared_data.md) reads already-arranged pages; [recorded responses](docs/recorded_responses.md) reads existing saved service responses. Both require separate files outside Git. Missing saved inputs produce errors rather than live requests. Prototype mode supplies sample content for local use and the test baseline; it does not demonstrate live integration.

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

The runner selects prototype mode before loading the private environment. Individual tests override the mode and use made-up source responses. Django creates and removes its test database. These tests do not verify connectivity to real services. See [development checks](docs/development_checks.md) for focused test selection and Python checks.

## Primary dependencies

This list follows declarations in [pyproject.toml](pyproject.toml), imports/configuration, and supporting packages in [uv.lock](uv.lock). There is no separate requirements file.

| Package | Purpose and where it is used |
| --- | --- |
| `Django` | Requests, templates, sessions, tests, and database tables in `config/` and `vivo_app/`. |
| `python-dotenv` | Environment loading in `config/settings.py`. |
| `httpx2` | Source and Turnstile HTTP requests in `source_requests.py` and `bot_detect.py`. |
| `django-browser-reload` | Optional local reload support when both debug and browser reload are enabled. |
| `pymysql` | Separate homepage book database; supplied by staging and prod. Django's own database uses SQLite. |
| `playwright`, `pillow` | Browser and image comparisons; Playwright is in local, Pillow in local and staging. |
| `trio` | Still directly declared. Possible HTTP-backend use needs review before removal; see [the review note](docs/code_retirement_review.md). |

The lockfile also records supporting packages, including Django's asgiref and sqlparse and the HTTP client's dependencies. Keep the local, staging, and prod groups. Ruff is configured in [ruff.toml](ruff.toml) and supplied separately; tests use Django and unittest.
